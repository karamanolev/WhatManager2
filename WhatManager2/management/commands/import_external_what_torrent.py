from optparse import make_option
import os
import os.path
import errno
import shutil

import bencode
from django.core.management.base import BaseCommand

from WhatManager2 import manage_torrent
from home.models import WhatTorrent, DownloadLocation, ReplicaSet, TransTorrent
from what_transcode.utils import get_info_hash


def safe_makedirs(p):
    try:
        os.makedirs(p)
    except OSError as ex:
        if ex.errno != errno.EEXIST:
            raise ex


class Command(BaseCommand):
    help = 'Moves existing torrent data and import the torrent in WM.'

    def add_arguments(self, parser):
        parser.add_argument('data_dir')
        parser.add_argument('torrent_file')
        parser.add_argument('--base-dir',
                            action='store_true',
                            dest='base_dir',
                            default=False,
                            help='Pass the containing directory of the torrent instead of the directory'
                                 ' itself. The name of the torrent will be automatically appended.')

    def __init__(self):
        super(Command, self).__init__()
        self.pseudo_request = lambda: None
        self.trans_instance = ReplicaSet.get_what_master().get_preferred_instance()
        self.download_location = DownloadLocation.get_what_preferred()
        self.data_path = None
        self.torrent_path = None
        self.torrent_info = None
        self.info_hash = None
        self.dest_path = None
        self.what_torrent = None

    def check_opts(self, options):
        if not os.path.isdir(options['data_dir']):
            return False
        if not os.path.isfile(options['torrent_file']):
            return False
        try:
            self.info_hash = get_info_hash(options['torrent_file'])
        except Exception:
            print('Invalid .torrent file.')
            return False
        return True

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
        os.makedirs(self.dest_path)
        os.chmod(self.dest_path, 0o777)
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
            shutil.move(f_path,f_dest_path)

    def handle(self, *args, **options):
        if not self.check_opts(options):
            print('Pass the torrent data directory as a first argument, ' \
                  'a path to the .torrent file as a second.')
            return
        self.data_path = options['data_dir']
        self.torrent_path = options['torrent_file']
        with open(self.torrent_path, 'rb') as f:
            self.torrent_info = bencode.bdecode(f.read())
        if options['base_dir']:
            self.data_path = os.path.join(self.data_path, self.torrent_info['info']['name'])
        print('Checking to see if torrent is already loaded into WM..')
        masters = list(ReplicaSet.get_what_master().transinstance_set.all())
        try:
            TransTorrent.objects.get(instance__in=masters, info_hash=self.info_hash)
            print('Torrent already added to WM. Skipping...')
            return False
        except TransTorrent.DoesNotExist:
            pass
        self.what_torrent = WhatTorrent.get_or_create(self.pseudo_request, info_hash=self.info_hash)
        if not self.check_files():
            return
        self.move_files()
        print('Adding torrent to WM...')
        manage_torrent.add_torrent(self.pseudo_request, self.trans_instance,
                                   self.download_location, self.what_torrent.id)
        print('Done!')
