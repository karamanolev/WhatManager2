from optparse import make_option
import os
import os.path
import errno
import shutil

import bencode
from django.core.management.base import BaseCommand

from WhatManager2 import manage_torrent
from WhatManager2.utils import wm_unicode, wm_str
from home.models import WhatTorrent, DownloadLocation, ReplicaSet, TransTorrent
from what_transcode.utils import get_info_hash


def safe_makedirs(p):
    try:
        os.makedirs(wm_str(p))
    except OSError as ex:
        if ex.errno != errno.EEXIST:
            raise ex


class Command(BaseCommand):
    option_list = BaseCommand.option_list + (
        make_option('--base-dir',
                    action='store_true',
                    dest='base_dir',
                    default=False,
                    help='Pass the containing directory of the torrent instead of the directory'
                         ' itself. The name of the torrent will be automatically appended.'),
    )
    help = u'Moves existing torrent data and import the torrent in WM.'

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

    def check_args(self, args):
        if len(args) != 2:
            return False
        if not os.path.isdir(args[0]):
            return False
        if not os.path.isfile(args[1]):
            return False
        try:
            self.info_hash = get_info_hash(args[1])
        except Exception:
            print u'Invalid .torrent file.'
            return False
        return True

    def get_unicode_torrent_files(self):
        files = []
        for f in self.torrent_info['info']['files']:
            nf = dict(f)
            nf['path'] = [wm_unicode(i) for i in nf['path']]
            files.append(nf)
        return files

    def check_files(self):
        print u'Checking for existing files...'
        if 'files' in self.torrent_info['info']:
            for f in self.get_unicode_torrent_files():
                f_path = os.path.join(self.data_path, *f['path'])
                print wm_str(u'Checking {0}'.format(f_path))
                if not os.path.isfile(wm_str(f_path)):
                    print wm_str(u'{0} does not exist. What are you giving me?'.format(f_path))
                    return False
        else:
            f_path = os.path.join(self.data_path, self.torrent_info['info']['name'])
            print wm_str(u'Checking {0}'.format(f_path))
            if not os.path.isfile(wm_str(f_path)):
                print wm_str(u'{0} does not exist. What are you giving me?'.format(f_path))
                return False
        print u'Creating destination directory...'
        self.dest_path = os.path.join(self.download_location.path, unicode(self.what_torrent.id))
        os.makedirs(wm_str(self.dest_path))
        os.chmod(self.dest_path, 0777)
        if 'files' in self.torrent_info['info']:
            self.dest_path = os.path.join(self.dest_path, wm_unicode(
                self.torrent_info['info']['name']))
            os.makedirs(wm_str(self.dest_path))
        print u'All torrent data files exist.'
        return True

    def move_files(self):
        print u'Moving files to new directory...'
        if 'files' in self.torrent_info['info']:
            for f in self.get_unicode_torrent_files():
                f_path = os.path.join(self.data_path, *f['path'])
                f_dest_path = os.path.join(self.dest_path, *f['path'])
                safe_makedirs(os.path.dirname(f_dest_path))
                shutil.move(wm_str(f_path), wm_str(f_dest_path))
        else:
            f_path = os.path.join(self.data_path, wm_unicode(self.torrent_info['info']['name']))
            f_dest_path = os.path.join(self.dest_path, wm_unicode(
                self.torrent_info['info']['name']))
            safe_makedirs(os.path.dirname(f_dest_path))
            shutil.move(wm_str(f_path), wm_str(f_dest_path))

    def handle(self, *args, **options):
        if not self.check_args(args):
            print u'Pass the torrent data directory as a first argument, ' \
                  u'a path to the .torrent file as a second.'
            return
        self.data_path, self.torrent_path = [wm_unicode(i) for i in args]
        with open(wm_str(self.torrent_path), 'rb') as f:
            self.torrent_info = bencode.bdecode(f.read())
        if options['base_dir']:
            self.data_path = os.path.join(self.data_path,
                                          wm_unicode(self.torrent_info['info']['name']))
        print u'Checking to see if torrent is already loaded into WM..'
        masters = list(ReplicaSet.get_what_master().transinstance_set.all())
        try:
            TransTorrent.objects.get(instance__in=masters, info_hash=self.info_hash)
            print u'Torrent already added to WM. Skipping...'
            return False
        except TransTorrent.DoesNotExist:
            pass
        self.what_torrent = WhatTorrent.get_or_create(self.pseudo_request, info_hash=self.info_hash)
        if not self.check_files():
            return
        self.move_files()
        print 'Adding torrent to WM...'
        manage_torrent.add_torrent(self.pseudo_request, self.trans_instance,
                                   self.download_location, self.what_torrent.id)
        print 'Done!'
