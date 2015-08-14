from __future__ import unicode_literals

import os
import shutil
from subprocess import call
import time

from celery import task
from django import db
from django.utils.functional import cached_property
import requests

from WhatManager2.settings import WHAT_ANNOUNCE, WHAT_UPLOAD_URL, TRANSCODER_ADD_TORRENT_URL, \
    TRANSCODER_HTTP_USERNAME, TRANSCODER_HTTP_PASSWORD, TRANSCODER_TEMP_DIR, \
    TRANSCODER_ERROR_OUTPUT, TRANSCODER_FORMATS
from WhatManager2.utils import get_artists
from home.models import get_what_client, DownloadLocation, ReplicaSet
from what_transcode.flac_lame import transcode_file
from what_transcode.utils import torrent_is_preemphasized, get_info_hash, html_unescape, \
    fix_pathname, extract_upload_errors, norm_dest_path, get_channels_number, recursive_chmod, \
    check_directory_tags_filenames, get_mp3_ids, safe_retrieve_new_torrent


source_roots, dest_upload_dir = None, None


def get_source_roots():
    global source_roots
    if source_roots is not None:
        return source_roots
    source_roots = [l.path for l in DownloadLocation.objects.filter(zone=ReplicaSet.ZONE_WHAT)]
    db.connection.close()
    return source_roots


def get_dest_upload_dir():
    global dest_upload_dir
    if dest_upload_dir is not None:
        return dest_upload_dir
    dest_upload_dir = DownloadLocation.get_what_preferred().path
    db.connection.close()
    return dest_upload_dir


class TranscodeSingleJob(object):
    def __init__(self, what, what_torrent, report_progress, source_dir, bitrate,
                 torrent_temp_dir=None):
        self.what = what
        self.force_warnings = False
        self.what_torrent = what_torrent
        self.report_progress = report_progress
        self.source_dir = source_dir
        self.bitrate = bitrate
        if torrent_temp_dir is None:
            self.torrent_temp_dir = os.path.join(TRANSCODER_TEMP_DIR, self.directory_name)
        else:
            self.torrent_temp_dir = torrent_temp_dir
        self.torrent_file_path = os.path.join(self.torrent_temp_dir,
                                              os.path.basename(self.torrent_temp_dir) + '.torrent')
        self.new_torrent = None
        self.new_torrent_info_hash = None

    def create_torrent(self):
        print 'Creating .torrent file...'
        args = [
            '-a', WHAT_ANNOUNCE,
            '-p',
            '-o', self.torrent_file_path,
            self.torrent_temp_dir,
        ]
        if call(['mktorrent'] + args) != 0:
            raise Exception('mktorrent returned non-zero')
        self.new_torrent_info_hash = get_info_hash(self.torrent_file_path)

    def _add_to_wm(self):
        new_id = self.new_torrent['torrent']['id']
        print 'Adding {0} to wm'.format(new_id)
        post_data = {
            'id': new_id,
            'tags': 'my',
            'dir': get_dest_upload_dir(),
        }
        response = requests.post(TRANSCODER_ADD_TORRENT_URL, data=post_data,
                                 auth=(TRANSCODER_HTTP_USERNAME, TRANSCODER_HTTP_PASSWORD))
        response_json = response.json()
        if not response_json['success']:
            raise Exception('Cannot add {0} to wm: {1}'.format(new_id, response.text))

    def add_to_wm(self):
        for i in range(3):
            try:
                self._add_to_wm()
                return
            except Exception:
                print 'Error adding to wm, trying again in 5 sec...'
                time.sleep(5)
        self._add_to_wm()

    def run(self):
        self.transcode_torrent()

        self.report_progress('{0} - creating torrent'.format(self.bitrate.upper()))
        self.create_torrent()

        self.report_progress('{0} - uploading to what.cd'.format(self.bitrate.upper()))
        self.upload_torrent()

        self.report_progress('{0} - moving to destination'.format(self.bitrate.upper()))
        self.move_torrent_to_dest()

        self.report_progress('{0} - adding to wm'.format(self.bitrate.upper()))
        self.add_to_wm()

    def retrieve_new_torrent(self, info_hash):
        if self.new_torrent:
            return
        self.new_torrent = safe_retrieve_new_torrent(self.what, info_hash)

    def move_torrent_to_dest(self):
        print 'Moving data to target location'

        os.remove(self.torrent_file_path)

        self.retrieve_new_torrent(self.new_torrent_info_hash)

        dest_path = os.path.join(get_dest_upload_dir(), str(self.new_torrent['torrent']['id']))
        try:
            os.makedirs(dest_path)
        except OSError:
            raise Exception('Dest torrent directory already exists.')
        shutil.move(self.torrent_temp_dir, dest_path)

        recursive_chmod(dest_path, 0777)

    @cached_property
    def directory_name(self):
        torrent = self.what_torrent
        artists = get_artists(torrent['group'])
        if len(artists) + len(torrent['group']['name']) > 80:
            if torrent['group']['musicInfo']['artists']:
                if len(torrent['group']['musicInfo']['artists']) > 1:
                    artists = 'Various Artists'
                else:
                    artists = torrent['group']['musicInfo']['artists'][0]['name']
            elif torrent['group']['musicInfo']['conductor']:
                if len(torrent['group']['musicInfo']['conductor']) > 1:
                    artists = 'Various Conductors'
                else:
                    artists = torrent['group']['musicInfo']['conductor'][0]['name']
        name = html_unescape(torrent['group']['name'])
        if len(name) > 70:
            name = name[:67] + '...'
        media = torrent['torrent']['media']
        year = torrent['torrent']['remasterYear'] or torrent['group']['year']
        return fix_pathname('{0} - {1} - {2} ({3} - MP3 - {4})'.format(
            artists, name, year, media, self.bitrate.upper()
        ))

    def upload_torrent(self):
        torrent = self.what_torrent
        print 'Sending request for upload to what.cd'

        payload_files = dict()
        payload_files['file_input'] = ('torrent.torrent', open(self.torrent_file_path, 'rb'))

        payload = dict()
        payload['submit'] = 'true'
        payload['auth'] = self.what.authkey
        payload['type'] = 'Music'
        payload['groupid'] = torrent['group']['id']
        payload['format'] = 'MP3'
        payload['bitrate'] = {
            'V0': 'V0 (VBR)',
            'V2': 'V2 (VBR)',
            '320': '320',
        }[self.bitrate]
        payload['media'] = torrent['torrent']['media']
        payload[
            'release_desc'] = 'Made with LAME 3.99.3 with -h using karamanolev\'s auto transcoder' \
                              ' from What.CD Torrent ID {0}.'.format(
            torrent['torrent']['id']) + ' Resampling or bit depth change (if needed) ' \
                                        'was done using SoX.'

        if torrent['torrent']['remastered']:
            payload['remaster'] = 'on'
            payload['remaster_year'] = torrent['torrent']['remasterYear']
            payload['remaster_title'] = torrent['torrent']['remasterTitle']
            payload['remaster_record_label'] = torrent['torrent']['remasterRecordLabel']
            payload['remaster_catalogue_number'] = torrent['torrent']['remasterCatalogueNumber']

        old_content_type = self.what.session.headers['Content-type']
        try:
            del self.what.session.headers['Content-type']

            response = self.what.session.post(WHAT_UPLOAD_URL, data=payload, files=payload_files)
            if response.url == WHAT_UPLOAD_URL:
                try:
                    errors = extract_upload_errors(response.text)
                except Exception:
                    errors = ''
                exception = Exception(
                    'Error uploading data to what.cd. Errors: {0}'.format('; '.join(errors)))
                exception.response_text = response.text
                with open(TRANSCODER_ERROR_OUTPUT, 'w') as error_file:
                    error_file.write(response.text.encode('utf-8'))
                raise exception
        except Exception as ex:
            time.sleep(2)
            try:
                self.retrieve_new_torrent(self.new_torrent_info_hash)
            except:
                raise ex
        finally:
            self.what.session.headers['Content-type'] = old_content_type

    def transcode_image(self, source_path):
        dest_rel_path = os.path.relpath(source_path, self.source_dir)
        dest_rel_path = norm_dest_path(os.path.basename(self.torrent_temp_dir), dest_rel_path)
        dest_path = os.path.join(self.torrent_temp_dir, dest_rel_path)

        try:
            os.makedirs(os.path.dirname(dest_path), 0777)
        except OSError:
            pass
        os.chmod(os.path.dirname(dest_path), 0777)

        shutil.copyfile(source_path, dest_path)
        os.chmod(dest_path, 0777)

    def transcode_flac(self, source_path):
        num_channels = get_channels_number(source_path)
        if num_channels == 1:
            if not self.force_warnings:
                raise Exception('Single channel file.')
        elif num_channels > 2:
            raise Exception('Not a 2-channel file.')

        dest_rel_path = os.path.relpath(source_path, self.source_dir)[:-4] + 'mp3'
        dest_rel_path = norm_dest_path(os.path.basename(self.torrent_temp_dir), dest_rel_path)
        dest_path = os.path.join(self.torrent_temp_dir, dest_rel_path)
        dest_path = os.path.join(os.path.dirname(dest_path),
                                 fix_pathname(os.path.basename(dest_path)))
        print 'Transcode'
        print ' ', source_path
        print ' ', dest_path
        transcode_file(source_path, dest_path, self.what_torrent['torrent']['media'], self.bitrate)

    def transcode_torrent(self):
        if os.path.exists(self.torrent_temp_dir):
            raise Exception('Target directory already exists. Do not run parallel jobs.')
        self.report_progress('Started transcoding to {0}'.format(self.bitrate.upper()))

        if not self.force_warnings:
            self.report_progress('Checking tags and filenames')
            check_directory_tags_filenames(self.source_dir)

        flac_paths = []
        for dirpath, dirnames, filenames in os.walk(self.source_dir):
            for filename in filenames:
                source_path = os.path.join(dirpath, filename)
                if filename.lower() in ['folder.jpg', 'folder.jpeg', 'cover.jpg', 'cover.jpeg',
                                        'front.jpg',
                                        'front.jpeg',
                                        'front cover.jpg', 'front cover.jpeg', 'art.jpg',
                                        'art.jpeg']:
                    self.transcode_image(source_path)
                elif filename.lower().endswith('.flac'):
                    flac_paths.append(source_path)
                elif '.part' in filename.lower():
                    raise Exception('There is a file that has not been fully downloaded. WTF?')

        if (len(flac_paths) <= 1) and (self.what_torrent['group']['releaseType'] != 9) and \
           (self.what_torrent['group']['releaseType'] != 13):  # 9 is Single, # 13 is Remix
            if self.force_warnings:
                print 'Warning: This is a single audio file torrent that is not a single or a ' \
                      'remix in What.cd. Will not transcode.'
            else:
                raise Exception('This is a single audio file torrent that is not a single or a '
                                'remix in What.cd. Will not transcode.')

        files_created = 0
        self.report_progress(
            '{0} - {1}/{2}'.format(self.bitrate.upper(), files_created, len(flac_paths)))
        for flac_path in flac_paths:
            self.transcode_flac(flac_path)
            files_created += 1
            self.report_progress(
                '{0} - {1}/{2}'.format(self.bitrate.upper(), files_created, len(flac_paths)))

        output_file_count = sum(
            len(filenames) for (dirpath, dirnames, filenames) in os.walk(self.torrent_temp_dir))
        if output_file_count < files_created:
            raise Exception(
                'Files in output dir too few. Expected {0}, saw {1}'.format(files_created,
                                                                            output_file_count))


class TranscodeJob(object):
    def __init__(self, what_id, celery_task=None):
        self.celery_task = celery_task
        self.what_id = str(what_id)
        self.what = None
        self.what_torrent = None
        self.what_group = None

        self.force_warnings = False
        self.force_v0 = False
        self.force_320 = False

    def report_progress(self, progress):
        print 'Progress: {0}'.format(progress)
        if self.celery_task:
            self.celery_task.update_state(state='PROGRESS', meta={'status_message': progress})

    @cached_property
    def source_dir(self):
        for root in get_source_roots():
            if self.what_id in os.listdir(root):
                torrent_root = os.path.join(root, self.what_id)
                for item in [os.path.join(torrent_root, f) for f in os.listdir(torrent_root)]:
                    if os.path.isdir(item):
                        return item
                return torrent_root
        raise Exception('Source directory for id {0} not found.'.format(self.what_id))

    def run(self):
        try:
            shutil.rmtree(TRANSCODER_TEMP_DIR)
        except OSError:
            pass

        # Pass an object that can hold the what_client property
        self.what = get_what_client(lambda: None)

        os.makedirs(TRANSCODER_TEMP_DIR)
        try:
            self.transcode_upload_lossless()
        finally:
            try:
                shutil.rmtree(TRANSCODER_TEMP_DIR)
            except OSError:
                pass

    def transcode_upload_lossless(self):
        print 'Will transcode {0}'.format(self.what_id)

        self.what_torrent = self.what.request('torrent', id=self.what_id)['response']
        what_group_id = self.what_torrent['group']['id']
        self.what_group = self.what.request('torrentgroup', id=what_group_id)['response']

        if self.what_torrent['torrent']['format'] != 'FLAC':
            raise Exception('Cannot transcode a non-FLAC torrent.')
        if not self.force_warnings and torrent_is_preemphasized(self.what_torrent):
            raise Exception('Cannot transcode a pre-emphasized torrent!')
        # if not self.force_warnings and self.what_torrent['torrent']['reported']:
        # raise Exception('Cannot transcode a reported torrent!')
        if not self.force_warnings and self.what_torrent['torrent']['scene']:
            raise Exception('Cannot transcode a scene torrent due to possible release group name '
                            'in the file names.')

        mp3_ids = get_mp3_ids(self.what_group, self.what_torrent)
        if self.force_v0 and 'V0' in mp3_ids:
            del mp3_ids['V0']
        if self.force_320 and '320' in mp3_ids:
            del mp3_ids['320']
        for bitrate in TRANSCODER_FORMATS:
            if bitrate not in mp3_ids:
                single_job = TranscodeSingleJob(self.what, self.what_torrent, self.report_progress,
                                                self.source_dir,
                                                bitrate)
                single_job.force_warnings = self.force_warnings
                single_job.run()
                print 'Uploaded {0}'.format(bitrate.upper())


@task(bind=True, track_started=True)
def transcode(self, what_id):
    job = TranscodeJob(what_id, self)
    job.run()
