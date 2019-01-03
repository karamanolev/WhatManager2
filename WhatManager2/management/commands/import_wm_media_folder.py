from optparse import make_option
from glob import glob
import os
import os.path
import errno
import shutil

import bencode
from bencode.BTL import BTFailure
from django.core.management.base import BaseCommand
from django.db.utils import OperationalError

from WhatManager2 import manage_torrent
from home.models import WhatTorrent, DownloadLocation, ReplicaSet, TransTorrent, RequestException
from what_transcode.utils import get_info_hash

def safe_makedirs(p):
    try:
        os.makedirs(p)
    except OSError as ex:
        if ex.errno != errno.EEXIST:
            raise ex


class Command(BaseCommand):
    help = 'Scans WM media folder from a previous installation and imports available torrents + data.'\
           ' Sorts and groups errored torrents into folders for easy post-import fixing/debugging'

    def add_arguments(self, parser):
        parser.add_argument('wm_media')
        parser.add_argument('--no-move',
                    action='store_false',
                    dest='move',
                    default=True,
                    help='Prevent import from moving and grouping folders when import errors occur')
            
    def __init__(self):
        super(Command, self).__init__()
        self.pseudo_request = lambda: None
        self.trans_instance = None
        self.download_location = DownloadLocation.get_what_preferred()
        self.data_path = None # folder containing files listed in torrent file
        self.torrent_info = None # torrent data
        self.torrent_id = None # torrent ID
        self.info_hash = None # hash of torrent data
        self.dest_path = None # path where transmission expects files to be
        self.what_torrent = None
        self.error_move = True # move folder when error is encountered

    def base_dir(self):
        return os.path.join(self.wm_media, self.torrent_id)

    def subfolder_move(self, subfolder, torrent_id):
        if not self.error_move:
            print('Skipping {}..'.format(torrent_id))
            return
        print('Moving {} to {} subfolder..'.format(torrent_id, subfolder))
        s = os.path.join(self.wm_media, torrent_id) # source
        d = os.path.join(self.wm_media, subfolder, torrent_id) # dest
        safe_makedirs(os.path.dirname(d))
        try:
            shutil.move(s, d)
        except Exception as e:
            shutil.rmtree(d)
            raise e

    def check_files(self):
        print('Checking for existing files...')
        if 'files' in self.torrent_info['info']:
            for f in self.torrent_info['info']['files']:
                f_path = os.path.join(self.data_path, *dict(f)['path'])
                print('Checking {0}'.format(f_path))
                if not os.path.isfile(f_path):
                    print('{0} does not exist. What are you giving me?'.format(f_path))
                    return False
        else:
            f_path = os.path.join(self.data_path, self.torrent_info['info']['name'])
            print('Checking {0}'.format(f_path))
            if not os.path.isfile(f_path):
                print('{0} does not exist. What are you giving me?'.format(f_path))
                return False
        print('Creating destination directory...')
        self.dest_path = os.path.join(self.download_location.path, str(self.what_torrent.id))
        try:
            os.makedirs(self.dest_path)
            os.chmod(self.dest_path, 0o777)
        except:
            print('Error: Could not create destination directory "{}"'.format(self.dest_path))
            return False
        if 'files' in self.torrent_info['info']:
            self.dest_path = os.path.join(self.dest_path, self.torrent_info['info']['name'])
            os.makedirs(self.dest_path)
        print('All torrent data files exist.')
        return True

    def move_files(self):
        print('Moving files to new directory...')
        if 'files' in self.torrent_info['info']:
            for f in self.torrent_info['info']['files']:
                f = dict(f)
                f_path = os.path.join(self.data_path, *f['path'])
                f_dest_path = os.path.join(self.dest_path, *f['path'])
                safe_makedirs(os.path.dirname(f_dest_path))
                shutil.move(f_path, f_dest_path)
        else:
            f_path = os.path.join(self.data_path, self.torrent_info['info']['name'])
            f_dest_path = os.path.join(self.dest_path, self.torrent_info['info']['name'])
            safe_makedirs(os.path.dirname(f_dest_path))
            shutil.move(f_path, f_dest_path)
        print('Success!')
        self.subfolder_move('imported', self.torrent_id)  

    def handle(self, *args, **options):
        if not os.path.isdir(options['wm_media']):
            print('Pass the directory containing your torrent directories from a previous WM' \
                  ' install. Subfolders of this directory should be named by torrent ID. After' \
                  ' import, all errored torrent/data sets will be organized into subfolders for' \
                  ' manual inspection/import.')
            return

        self.wm_media = options['wm_media']
        self.error_move = options['move']

        for self.torrent_id in next(os.walk(self.wm_media))[1]:
            try:
                # Is this actually a directory?
                if not os.path.isdir(self.base_dir()):
                    print('"{}" is not a valid directory. Skipping..'.format(self.base_dir()))
                    continue

                # Get all torrents
                torrents = []
                hashes = []
                for p in os.listdir(self.base_dir()):
                    if p.endswith('.torrent') and not p.startswith('._'):
                        try:
                            p = os.path.join(self.base_dir(), p)
                            hashes.append(get_info_hash(p))
                            torrents.append(p)
                        except IOError:
                            print(('Warning: Invalid torrent found in {}'.format(self.torrent_id)))
                            continue
                        except  BTFailure as e:
                            print(('Warning: {}. Invalid torrent found in {}'.format(str(e), self.torrent_id)))
                            continue
    
                # Are there any valid torrents?
                if len(torrents) == 0:
                    if self.torrent_id.isdigit():
                        print('Error: No valid torrent files found in "{}".'.format(self.base_dir()))
                        self.subfolder_move('no_torrents', self.torrent_id)
                    continue

                # Are there multiple unique torrents?
                if len(set(hashes)) > 1:
                    print('Error: Multiple unique torrents found')
                    self.subfolder_move('multiple_torrent', self.torrent_id)
                    continue

            except UnicodeDecodeError as e:
                print('UnicodeDecodeError: Please import manually. Skipping..')
                continue

            with open(torrents[0], 'rb') as f:
                try:
                    self.torrent_info = bencode.bdecode(f.read())
                    self.info_hash = get_info_hash(torrents[0])
                except:
                    print('Error: Invalid torrent file.')
                    self.subfolder_move('invalid_torrent', self.torrent_id)
                    continue
                self.data_path = os.path.join(self.base_dir(), self.torrent_info['info']['name'])
            print('Checking to see if torrent is already loaded into WM..')
            masters = list(ReplicaSet.get_what_master().transinstance_set.all())
            try:
                TransTorrent.objects.get(instance__in=masters, info_hash=self.info_hash)
                print('Error: Torrent already added to WM.')
                self.subfolder_move('already_added', self.torrent_id)
                continue
            except TransTorrent.DoesNotExist:
                pass
            try:
                self.what_torrent = WhatTorrent.get_or_create(self.pseudo_request, info_hash=self.info_hash)
            except RequestException as e:
                if 'bad hash' in str(e):
                    print('Error: Bad hash. Torrent may have been trumped/deleted.'.format(str(e)))
                    self.subfolder_move('bad_hash', self.torrent_id)
                    continue
                else:
                    raise e
            except OperationalError as e:
                if 'MySQL' in str(e):
                    print('Error: {}. Please check {} manually.'.format(str(e), self.torrent_id))
                    self.subfolder_move('mysql_error', self.torrent_id)
                    continue
                else:
                    raise e
            if not self.check_files():
                print('Error: File check failed.')
                try:
                    self.subfolder_move('file_check_fail', self.torrent_id)
                except UnicodeDecodeError as e:
                    print('UnicodeDecodeError. Move failed. Please manually check {} Skipping..'.format(self.torrent_id))
                continue
            self.move_files()
            print('Adding torrent to WM...')
            self.trans_instance = ReplicaSet.get_what_master().get_preferred_instance()
            manage_torrent.add_torrent(self.pseudo_request, self.trans_instance,
                                    self.download_location, self.what_torrent.id)
            print('Done!')
