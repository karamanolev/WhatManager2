import os
import shutil
import time
import ujson
from html.parser import HTMLParser
from base64 import b64decode

import bencode
from django.conf import settings
from django.core.management.base import BaseCommand
from html2bbcode.parser import HTML2BBCode

from WhatManager2.manage_torrent import add_torrent
from books.utils import call_mktorrent
from home.models import ReplicaSet, get_what_client, DownloadLocation, WhatTorrent, \
    RequestException, \
    BadIdException
from wcd_pth_migration import torrentcheck
from wcd_pth_migration.logfile import LogFile, UnrecognizedRippingLogException, \
    InvalidRippingLogException
from wcd_pth_migration.models import DownloadLocationEquivalent, WhatTorrentMigrationStatus, \
    TorrentGroupMapping
from wcd_pth_migration.utils import generate_spectrals_for_dir, normalize_for_matching
from what_transcode.utils import extract_upload_errors, safe_retrieve_new_torrent, \
    get_info_hash_from_data, recursive_chmod, pthify_torrent

html_to_bbcode = HTML2BBCode()
html_parser = HTMLParser()
dummy_request = lambda: None  # To hold the what object


def extract_new_artists_importance(group_info):
    artists = []
    importance = []
    for importance_key, artist_list in list(group_info['musicInfo'].items()):
        importance_value = {
            'artists': 1,  # Main
            'with': 2,  # Guest
            'composers': 4,  # Composer
            'conductor': 5,  # Conductor
            'dj': 6,  # DJ / Compiler
            'remixedBy': 3,  # Remixer
            'producer': 7,  # Producer
        }[importance_key]
        for artist_item in artist_list:
            artists.append(artist_item['name'])
            importance.append(str(importance_value))
    return artists, importance


def format_bytes_pth(length):
    mb = length / 1024.0 / 1024.0
    suffix = 'MB'
    if mb >= 1024:
        mb /= 1024.0
        suffix = 'GB'
    return '{:.2f} {}'.format(mb, suffix)


def fix_duplicate_newlines(s):
    return s.replace('\r', '').replace('\n\n', '\n')


class TorrentMigrationJob(object):
    REAL_RUN = True

    def __init__(self, what, location_mapping, data, flac_only):
        self.flac_only = flac_only
        self.what = what
        self.location_mapping = location_mapping
        self.data = data
        self.what_torrent = self.data['what_torrent']
        self.what_torrent_info = ujson.loads(self.what_torrent['info'])
        self.full_location = os.path.join(self.data['location']['path'],
            str(self.what_torrent['id']))
        self.torrent_dict = bencode.bdecode(b64decode(self.what_torrent['torrent_file']))
        self.torrent_name = self.torrent_dict['info']['name']
        self.torrent_new_name = self.torrent_name
        self.torrent_dir_path = os.path.join(self.full_location.encode('utf-8'), self.torrent_name)

        self.new_torrent = None
        self.log_files = set()
        self.log_files_full_paths = []
        self.torrent_file_new_data = None
        self.torrent_new_infohash = None
        self.payload = None
        self.payload_files = None
        self.existing_new_group = None
        self.full_new_location = None

    def check_valid(self):
        print('Verifying torrent data...')
        try:
            if not torrentcheck.verify(self.torrent_dict['info'], self.full_location):
                raise Exception('Torrent does not verify')
        except Exception as ex:
            WhatTorrentMigrationStatus.objects.create(
                what_torrent_id=self.what_torrent['id'],
                status=WhatTorrentMigrationStatus.STATUS_FAILED_VALIDATION
            )
            input('Verification threw {}. Press enter to continue.'.format(ex))
            return False
        print('Hash matching')
        torrent_file_set = {'/'.join(f['path']) for f in self.torrent_dict['info']['files']}
        for dirpath, dirnames, filenames in os.walk(self.torrent_dir_path):
            for filename in filenames:
                abs_path = os.path.join(dirpath, filename)
                file_path = os.path.relpath(abs_path, self.torrent_dir_path)
                if file_path not in torrent_file_set:
                    raise Exception(
                        'Extraneous file: {}/{}'.format(self.torrent_dir_path, file_path))
                if filename.lower().endswith('.log'):
                    print('Candidate log file', abs_path)
                    with open(abs_path, 'r') as log_f:
                        try:
                            self.log_files.add(LogFile(log_f.read()))
                        except UnrecognizedRippingLogException:
                            print('Skipping: unrecognized')
                            pass
                        except InvalidRippingLogException:
                            input('Log file unrecognized!')
                    self.log_files_full_paths.append(abs_path)
        print('No extraneous files')
        print('Torrent verification complete')
        return True

    def mktorrent(self):
        print('Creating torrent file...')
        torrent_temp_filename = 'temp.torrent'
        try:
            os.remove(torrent_temp_filename)
        except OSError:
            pass
        call_mktorrent(self.torrent_dir_path,
                       torrent_temp_filename,
                       settings.WHAT_ANNOUNCE,
                       self.torrent_new_name)
        with open(torrent_temp_filename, 'rb') as torrent_file:
            self.torrent_file_new_data = pthify_torrent(torrent_file.read())
            self.torrent_new_infohash = get_info_hash_from_data(self.torrent_file_new_data)
            print('New info hash is: ', self.torrent_new_infohash)
        print('Torrent file created')

    def retrieve_new_torrent(self, info_hash):
        if self.new_torrent is None:
            self.new_torrent = safe_retrieve_new_torrent(self.what, info_hash)
            self.migration_status.pth_torrent_id = self.new_torrent['torrent']['id']
            self.migration_status.save()

    def set_new_location(self):
        mapped_location = self.location_mapping[self.data['location']['path']]
        self.new_location_obj = DownloadLocation.objects.get(path=mapped_location)
        self.full_new_location = os.path.join(
            mapped_location,
            str(self.new_torrent['torrent']['id'])
        )

    def prepare_payload(self):
        t_info = self.what_torrent_info['torrent']
        g_info = self.what_torrent_info['group']

        if g_info['categoryName'] != 'Music':
            raise Exception('Can only upload Music torrents for now')
        if t_info['format'] == 'MP3' and t_info['encoding'] not in ['V0 (VBR)', '320']:
            raise Exception('Please let\'s not upload this bitrate MP3')

        payload = dict()
        payload['submit'] = 'true'
        payload['auth'] = self.what.authkey
        payload['type'] = '0'  # Music
        if self.existing_new_group:
            payload['groupid'] = self.existing_new_group['group']['id']
        else:
            payload['artists[]'], payload['importance[]'] = extract_new_artists_importance(g_info)
            payload['title'] = html_parser.unescape(g_info['name'])
            payload['year'] = str(g_info['year'])
            payload['record_label'] = g_info['recordLabel'] or ''
            payload['catalogue_number'] = g_info['catalogueNumber'] or ''
            payload['releasetype'] = str(g_info['releaseType'])
            payload['tags'] = ','.join(g_info['tags'])
            payload['image'] = g_info['wikiImage'] or ''
            payload['album_desc'] = fix_duplicate_newlines(html_to_bbcode.feed(g_info['wikiBody']))
        if t_info['scene']:
            payload['scene'] = 'on'
        payload['format'] = t_info['format']
        payload['bitrate'] = t_info['encoding']
        payload['media'] = t_info['media']
        payload['release_desc'] = fix_duplicate_newlines(html_to_bbcode.feed(
            t_info['description']).replace('karamanolevs', 'karamanolev\'s'))

        if t_info['remastered']:
            payload['remaster'] = 'on'
            payload['remaster_year'] = t_info['remasterYear']
            payload['remaster_title'] = t_info['remasterTitle']
            payload['remaster_record_label'] = t_info['remasterRecordLabel']
            payload['remaster_catalogue_number'] = t_info['remasterCatalogueNumber']
        self.payload = payload

    def prepare_payload_files(self):
        payload_files = []
        payload_files.append(('file_input', ('torrent.torrent', self.torrent_file_new_data)))
        if self.what_torrent_info['torrent']['format'] == 'FLAC':
            for log_file_path in self.log_files_full_paths:
                print('Log file {}'.format(log_file_path))
                print(''.join(list(open(log_file_path))[:4]))
                print()
                response = input('Add to upload [y/n]: ')
                if response == 'y':
                    payload_files.append(('logfiles[]', ('logfile.log', open(log_file_path, 'rb'))))
                elif response == 'n':
                    pass
                else:
                    raise Exception('Bad response')
        self.payload_files = payload_files

    def perform_upload(self):
        if self.REAL_RUN:
            old_content_type = self.what.session.headers['Content-type']
            try:
                del self.what.session.headers['Content-type']

                response = self.what.session.post(
                    settings.WHAT_UPLOAD_URL, data=self.payload, files=self.payload_files)
                if response.url == settings.WHAT_UPLOAD_URL:
                    try:
                        errors = extract_upload_errors(response.text)
                    except Exception:
                        errors = ''
                    exception = Exception(
                        'Error uploading data to what.cd. Errors: {0}'.format('; '.join(errors)))
                    exception.response_text = response.text
                    with open('uploaded_error.html', 'w') as error_file:
                        error_file.write(response.text.encode('utf-8'))
                    raise exception
            except Exception as ex:
                time.sleep(2)
                try:
                    self.retrieve_new_torrent(self.torrent_new_infohash)
                except:
                    raise ex
            finally:
                self.retrieve_new_torrent(self.torrent_new_infohash)
                self.what.session.headers['Content-type'] = old_content_type
            self.migration_status.status = WhatTorrentMigrationStatus.STATUS_UPLOADED
            self.migration_status.save()
        else:
            print('Ready with payload')
            print(ujson.dumps(self.payload, indent=4))

    def get_total_size(self):
        return sum(f['length'] for f in self.torrent_dict['info']['files'])

    def print_info(self):
        if 'groupid' in self.payload:
            print('Part of existing torrent group')
            print('Artists:       ', ','.join(
                artist['name'] for artist in
                self.existing_new_group['group']['musicInfo']['artists']
            ))
            print('Album title:   ', self.existing_new_group['group']['name'])
            print('Year:          ', self.existing_new_group['group']['year'])
            print('Record label:  ', self.existing_new_group['group']['recordLabel'])
            print('Catalog number:', self.existing_new_group['group']['catalogueNumber'])
            print('Release type:  ', self.existing_new_group['group']['releaseType'])
            print()
        else:
            print('Artists:       ', ','.join(
                artist['name'] for artist, importance in zip(
                    self.payload['artists[]'], self.payload['importance[]'])
                if importance == 1  # Main
            ))
            print('Album title:   ', self.payload['title'])
            print('Year:          ', self.payload['year'])
            print('Record label:  ', self.payload['record_label'])
            print('Catalog number:', self.payload['catalogue_number'])
            print('Release type:  ', self.payload['releasetype'])
            print()
        if 'remaster' in self.payload:
            print('  Edition information')
            print('  Year:          ', self.payload['remaster_year'])
            print('  Record label:  ', self.payload['remaster_record_label'])
            print('  Catalog number:', self.payload['remaster_catalogue_number'])
            print()
        print('Scene:         ', 'yes' if 'scene' in self.payload else 'no')
        print('Format:        ', self.payload['format'])
        print('Bitrate:       ', self.payload['bitrate'])
        print('Media:         ', self.payload['media'])
        if 'groupid' not in self.payload:
            print('Tags:          ', self.payload['tags'])
            print('Image:         ', self.payload['image'])
            print('Album desc:    ', self.payload['album_desc'])
        print('Release desc:  ', self.payload['release_desc'])

    def find_existing_torrent_by_hash(self):
        try:
            existing_by_hash = self.what.request('torrent', hash=self.torrent_new_infohash)
            if existing_by_hash['status'] == 'success':
                self.new_torrent = existing_by_hash['response']
        except RequestException:
            pass
        return None

    def find_existing_torrent_group(self):
        if self.existing_new_group is not None:
            return

        existing_group_id = None

        group_id = self.what_torrent_info['group']['id']
        try:
            mapping = TorrentGroupMapping.objects.get(what_group_id=group_id)
            mapping_group = self.what.request('torrentgroup', id=mapping.pth_group_id)['response']
            if mapping_group['group']['id'] != mapping.pth_group_id:
                raise Exception('NOOOOO THIS CANNOT HAPPEN {} {}!'.format(
                    mapping_group['group']['id'],
                    mapping.pth_group_id,
                ))
            existing_group_id = mapping.pth_group_id
            print('Found torrent group mapping with {}'.format(existing_group_id))
        except TorrentGroupMapping.DoesNotExist:
            pass
        except BadIdException:
            print('Mapping has gone bad, deleting...')
            mapping.delete()

        if existing_group_id is None:
            group_year = self.what_torrent_info['group']['year']
            group_name = html_parser.unescape(self.what_torrent_info['group']['name']).lower()
            search_str = '{} {}'.format(group_name, str(group_year))
            results = self.what.request('browse', searchstr=search_str)['response']['results']
            for result in results:
                if html_parser.unescape(result['groupName']).lower() == group_name and \
                                result['groupYear'] == group_year:
                    if not existing_group_id:
                        existing_group_id = result['groupId']
                        print('Found existing group', existing_group_id)
                    else:
                        print('Multiple matching existing groups!!!!!!!!!!')
                        existing_group_id = None
                        break
        if existing_group_id is None:
            existing_group_id = input('Enter existing group id (empty if non-existent): ')
            if existing_group_id:
                TorrentGroupMapping.objects.get_or_create(
                    what_group_id=self.what_torrent_info['group']['id'],
                    pth_group_id=existing_group_id
                )
        if existing_group_id:
            self.existing_new_group = self.existing_new_group = self.what.request(
                'torrentgroup', id=existing_group_id)['response']

    def find_matching_torrent_within_group(self):
        t_info = self.what_torrent_info['torrent']
        g_info = self.what_torrent_info['group']

        existing_torrent_id = None
        for torrent in self.existing_new_group['torrents']:
            if torrent['size'] == t_info['size']:
                if not existing_torrent_id:
                    existing_torrent_id = torrent['id']
                else:
                    input('Warning: Multiple matching torrent sizes ({} and {})! '
                              'Taking first.'.format(
                        existing_torrent_id, torrent['id']))
        return existing_torrent_id

    def find_existing_torrent_within_group(self):
        t_info = self.what_torrent_info['torrent']
        g_info = self.what_torrent_info['group']

        existing_torrent_id = None
        original_catalog_number = normalize_for_matching(
            t_info['remasterCatalogueNumber'] or g_info['catalogueNumber'])
        for torrent in self.existing_new_group['torrents']:
            torrent_catalog_number = normalize_for_matching(
                torrent['remasterCatalogueNumber'] or
                self.existing_new_group['group']['catalogueNumber'])
            torrent_catalog_number = torrent_catalog_number.lower()
            matching_media_format = \
                t_info['media'] == torrent['media'] and \
                t_info['format'] == torrent['format'] and \
                t_info['encoding'] == torrent['encoding']

            # Comparing log files
            if torrent['format'] == 'FLAC' and t_info['format'] == 'FLAC' and len(self.log_files):
                try:
                    torrent_log_files = {
                        LogFile(l) for l in
                        self.what.request('torrentlog', torrentid=torrent['id'])['response']
                        }
                    if torrent_log_files == self.log_files:
                        print('Found matching log files with {}!!!'.format(torrent['id']))
                        if not existing_torrent_id:
                            existing_torrent_id = torrent['id']
                            continue
                        else:
                            print('Multiple existing catalog numbers ({} and {})'.format(
                                existing_torrent_id, torrent['id']))
                            existing_torrent_id = input('Enter torrent id if dup: ')
                    else:
                        if len(torrent_log_files.intersection(self.log_files)):
                            input('Log file sets are not exact matches, '
                                      'but found matching log files between ours and {}!!!'.format(
                                torrent['id']))
                except InvalidRippingLogException:
                    input('Log file for {} invalid!'.format(torrent['id']))
                except UnrecognizedRippingLogException:
                    input('Log file for {} unrecognized!'.format(torrent['id']))

            if original_catalog_number == torrent_catalog_number and matching_media_format:
                if not existing_torrent_id:
                    existing_torrent_id = torrent['id']
                    continue
                else:
                    print('Multiple existing catalog numbers ({} and {})'.format(
                        existing_torrent_id, torrent['id']))
                    existing_torrent_id = input('Enter torrent id if dup: ')

        return existing_torrent_id

    def find_dupes(self):
        response = None
        existing_torrent_id = None

        t_info = self.what_torrent_info['torrent']
        g_info = self.what_torrent_info['group']
        remaster = t_info['remastered']
        print('What id:      ', self.what_torrent['id'])
        print('Title:        ', '; '.join(
            a['name'] for a in g_info['musicInfo']['artists']), '-', html_parser.unescape(
            g_info['name']))
        print('Year:         ', g_info['year'])
        print('Media:        ', t_info['media'])
        print('Format:       ', t_info['format'])
        print('Bitrate:      ', t_info['encoding'])
        print('Remaster:     ', 'yes ({})'.format(t_info['remasterYear']) if remaster else 'no')
        print('Label:        ', t_info['remasterRecordLabel'] if remaster else g_info['recordLabel'])
        print('Cat no:       ', t_info['remasterCatalogueNumber'] if remaster else g_info[
            'catalogueNumber'])
        print('Remaster desc:', t_info['remasterTitle'])
        print('Torrent name: ', self.torrent_name)
        print('Torrent size: ', format_bytes_pth(self.get_total_size()))
        print()

        self.find_existing_torrent_by_hash()
        if self.new_torrent:
            print('Found existing torrent by hash ' + str(
                self.new_torrent['torrent']['id']) + ' reseeding!!!')
            self.migration_status = WhatTorrentMigrationStatus.objects.create(
                what_torrent_id=self.what_torrent['id'],
                status=WhatTorrentMigrationStatus.STATUS_RESEEDED,
                pth_torrent_id=self.new_torrent['torrent']['id'],
            )
            return True

        self.find_existing_torrent_group()
        if self.existing_new_group:
            matching_torrent_id = self.find_matching_torrent_within_group()
            if matching_torrent_id:
                print('Found matching torrent id:', matching_torrent_id)
                response = 'reseed'
            else:
                existing_torrent_id = self.find_existing_torrent_within_group()
                if existing_torrent_id:
                    print('Found existing torrent id:', existing_torrent_id)
                    response = 'dup'

        if not response:
            response = input('Choose action [up/dup/skip/skipp/reseed/changetg]: ')
        else:
            if response != 'reseed':
                new_response = input(response + '. Override: ')
                if new_response:
                    response = new_response

        if response == 'up':
            self.migration_status = WhatTorrentMigrationStatus(
                what_torrent_id=self.what_torrent['id'],
                status=WhatTorrentMigrationStatus.STATUS_PROCESSING,
            )
            return True
        elif response == 'reseed':
            if not matching_torrent_id:
                matching_torrent_id = int(input('Enter matching torrent id: '))
            existing_torrent = WhatTorrent.get_or_create(dummy_request, what_id=matching_torrent_id)
            existing_info = bencode.bdecode(existing_torrent.torrent_file_binary)
            success = False
            try:
                if not torrentcheck.verify(existing_info['info'], self.full_location):
                    raise Exception('Torrent does not verify')
                success = True
            except Exception as ex:
                print('Existing torrent does not verify with', ex)
            if success:
                self.new_torrent = self.what.request('torrent', id=matching_torrent_id)['response']
                self.migration_status = WhatTorrentMigrationStatus.objects.create(
                    what_torrent_id=self.what_torrent['id'],
                    status=WhatTorrentMigrationStatus.STATUS_RESEEDED,
                    pth_torrent_id=matching_torrent_id,
                )
                return True
        self.migration_status = WhatTorrentMigrationStatus(
            what_torrent_id=self.what_torrent['id'],
        )
        if response == 'dup':
            if not existing_torrent_id:
                existing_torrent_id = int(input('Enter existing torrent id: '))
            existing_torrent = self.what.request('torrent', id=existing_torrent_id)['response']
            self.migration_status.status = WhatTorrentMigrationStatus.STATUS_DUPLICATE
            self.migration_status.pth_torrent_id = existing_torrent_id
            TorrentGroupMapping.objects.get_or_create(
                what_group_id=self.what_torrent_info['group']['id'],
                pth_group_id=existing_torrent['group']['id'],
            )
        elif response == 'skip':
            self.migration_status.status = WhatTorrentMigrationStatus.STATUS_SKIPPED
        elif response == 'skipp':
            self.migration_status.status = WhatTorrentMigrationStatus.STATUS_SKIPPED_PERMANENTLY
        elif response == 'reseed':
            self.migration_status.status = WhatTorrentMigrationStatus.STATUS_DUPLICATE
            self.migration_status.pth_torrent_id = matching_torrent_id
        elif response == 'changetg':
            existing_group_id = input('Enter existing group id (empty if non-existent): ')
            if existing_group_id:
                self.existing_new_group = self.existing_new_group = self.what.request(
                    'torrentgroup', id=existing_group_id)['response']
            return self.find_dupes()
        else:
            raise Exception('Unknown response')
        self.migration_status.save()
        return False

    def _add_to_wm(self):
        new_id = self.new_torrent['torrent']['id']
        instance = ReplicaSet.get_what_master().get_preferred_instance()
        trans_torrent = add_torrent(dummy_request, instance, self.new_location_obj, new_id)
        print('Added to', trans_torrent.instance.name)

    def add_to_wm(self):
        for i in range(3):
            try:
                self._add_to_wm()
                return
            except Exception:
                print('Error adding to wm, trying again in 5 sec...')
                time.sleep(5)
        self._add_to_wm()

    def enhance_torrent_data(self):
        if self.what_torrent_info['torrent']['media'] == 'Blu-ray':
            self.what_torrent_info['torrent']['media'] = 'Blu-Ray'
        if not any(self.what_torrent_info['group']['tags']):
            tags = input('Enter tags (comma separated): ').split(',')
            self.what_torrent_info['group']['tags'] = tags
        if len(self.what_torrent_info['group']['wikiBody']) < 10:
            wiki_body = input('Enter wiki body: ')
            self.what_torrent_info['group']['wikiBody'] = wiki_body
        if 'tinypic.com' in self.what_torrent_info['group']['wikiImage'].lower():
            self.what_torrent_info['group']['wikiImage'] = ''
        if self.what_torrent_info['torrent']['remastered'] and not \
                self.what_torrent_info['torrent']['remasterYear']:
            remaster_year = input('Enter remaster year: ')
            self.what_torrent_info['torrent']['remasterYear'] = remaster_year

    def generate_spectrals(self):
        print('Generating spectrals...')
        generate_spectrals_for_dir(self.full_location)

    def save_torrent_group_mapping(self):
        TorrentGroupMapping.objects.get_or_create(
            what_group_id=self.what_torrent_info['group']['id'],
            pth_group_id=self.new_torrent['group']['id']
        )

    def process(self):
        what_torrent_id = self.what_torrent['id']

        if self.what_torrent_info['group']['categoryName'] != 'Music':
            print('Skipping non-Music torrent', what_torrent_id)
            return

        if self.flac_only and self.what_torrent_info['torrent']['format'] != 'FLAC':
            print('Skipping non-FLAC torrent', what_torrent_id)
            return

        try:
            status = WhatTorrentMigrationStatus.objects.get(what_torrent_id=what_torrent_id)
            if status.status == WhatTorrentMigrationStatus.STATUS_COMPLETE:
                print('Skipping complete torrent', what_torrent_id)
                return
            elif status.status == WhatTorrentMigrationStatus.STATUS_DUPLICATE:
                print('Skipping duplicate torrent', what_torrent_id)
                return
            elif status.status == WhatTorrentMigrationStatus.STATUS_SKIPPED:
                print('Skipping skipped torrent', what_torrent_id)
                return
            elif status.status == WhatTorrentMigrationStatus.STATUS_SKIPPED_PERMANENTLY:
                print('Skipping permanently skipped torrent', what_torrent_id)
                return
            elif status.status == WhatTorrentMigrationStatus.STATUS_FAILED_VALIDATION:
                print('Skipping failed validation torrent', what_torrent_id)
                return
            elif status.status == WhatTorrentMigrationStatus.STATUS_RESEEDED:
                print('Skipping reseeded torrent', what_torrent_id)
                return
            else:
                raise Exception('Not sure what to do with status {} on {}'.format(
                    status.status, what_torrent_id))
        except WhatTorrentMigrationStatus.DoesNotExist:
            pass
        if not self.check_valid():
            return
        self.mktorrent()
        if not self.find_dupes():
            return
        if not self.new_torrent:
            self.enhance_torrent_data()
            self.prepare_payload()
            self.print_info()
            self.prepare_payload_files()
            self.generate_spectrals()
            input('Will perform upload (CHECK THE SPECTRALS)...')
            self.perform_upload()
        self.set_new_location()
        if self.REAL_RUN:
            os.makedirs(self.full_new_location)
            shutil.move(self.torrent_dir_path, self.full_new_location)
            try:
                recursive_chmod(self.full_new_location, 0o777)
            except OSError:
                print('recursive_chmod failed')
        else:
            print('os.makedirs({})'.format(self.full_new_location))
            print('shutil.move({}, {})'.format(self.torrent_dir_path, self.full_new_location))
            print('recursive_chmod({}, 0777)'.format(self.full_new_location))
        if self.REAL_RUN:
            self.add_to_wm()
            self.migration_status.status = WhatTorrentMigrationStatus.STATUS_COMPLETE
            self.migration_status.save()
            self.save_torrent_group_mapping()
        else:
            print('add_to_wm()')
        print()
        print()


class Command(BaseCommand):
    help = 'Export transmission torrents and what torrents'

    def add_arguments(self, parser):
        parser.add_argument('--flac-only', action='store_true', default=False)

    def handle(self, *args, **options):
        print('Initiating what client...')
        what = get_what_client(dummy_request, True)
        index_response = what.request('index')
        print('Status:', index_response['status'])
        print('Scanning replica sets...')
        try:
            ReplicaSet.objects.get(zone='what.cd')
            raise Exception('Please delete your what.cd replica set now')
        except ReplicaSet.DoesNotExist:
            pass
        try:
            pth_replica_set = ReplicaSet.get_what_master()
            if pth_replica_set.transinstance_set.count() < 1:
                raise ReplicaSet.DoesNotExist()
        except ReplicaSet.DoesNotExist:
            raise Exception('Please get your PTH replica set ready')
        print('Scanning locations...')
        location_mapping = {}
        with open('what_manager2_torrents.jsonl', 'rb') as torrents_input:
            for line in torrents_input:
                data = ujson.loads(line)
                location_path = data['location']['path']
                if location_path not in location_mapping:
                    try:
                        new_location = DownloadLocationEquivalent.objects.get(
                            old_location=location_path).new_location
                    except DownloadLocationEquivalent.DoesNotExist:
                        new_location = input(
                            'Enter the new location to map to {}: '.format(location_path))
                        DownloadLocationEquivalent.objects.create(
                            old_location=location_path,
                            new_location=new_location,
                        )
                    location_mapping[location_path] = new_location
        print('Location mappings:')
        for old_location, new_location in list(location_mapping.items()):
            try:
                DownloadLocation.objects.get(zone='redacted.ch', path=new_location)
            except DownloadLocation.DoesNotExist:
                raise Exception(
                    'Please create the {} location in the DB in zone redacted.ch'.format(
                        new_location))
            print(old_location, '=', new_location)
        with open('what_manager2_torrents.jsonl', 'rb') as torrents_input:
            for line in torrents_input:
                data = ujson.loads(line)
                migration_job = TorrentMigrationJob(what, location_mapping, data,
                                                    flac_only=options['flac_only'])
                migration_job.process()
