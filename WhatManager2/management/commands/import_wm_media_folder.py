from optparse import make_option
from glob import glob
import hashlib
import os
import os.path
import errno
import shutil

import bencode
from django.core.management.base import BaseCommand

from WhatManager2 import manage_torrent
from WhatManager2.utils import wm_unicode, wm_str
from home.models import WhatTorrent, DownloadLocation, ReplicaSet, TransTorrent


def safe_makedirs(p):
    try:
        os.makedirs(wm_str(p))
    except OSError as ex:
        if ex.errno != errno.EEXIST:
            raise ex


class Command(BaseCommand):
    help = u'Scans previous WM media folder and imports available torrents + data'

    def __init__(self):
        super(Command, self).__init__()
        self.pseudo_request = lambda: None
        self.trans_instance = ReplicaSet.get_what_master().get_preferred_instance()
        self.download_location = DownloadLocation.get_what_preferred()
        self.wm_media = None
        self.data_path = None
        self.base_dir = None
        self.torrent_path = None
        self.torrent_info = None
        self.info_hash = None
        self.dest_path = None
        self.what_torrent = None

    def check_args(self, args):
        if len(args) != 1:
            return False
        if not os.path.isdir(args[0]):
            return False

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
        print u'..Success! Moving data directory to "imported" folder..'
        safe_makedirs(os.path.dirname(os.path.join(self.wm_media, 'imported')))
        shutil.move(wm_str(self.data_path), os.path.join(self.wm_media, 'imported', self.base_dir))

    def handle(self, *args, **options):
        if not self.check_args(args):
            print u'Pass the directory containing your torrent directories from a previous WM' \
                  u' install. Subfolders of this directory should be named by torrent ID.'
            return
        self.wm_media = wm_unicode(args[0])

        for self.base_dir in next(os.walk(self.wm_media))[1]:
            self.data_path = wm_unicode(os.path.join(args[0], self.base_dir))
            if not os.path.isdir(self.data_path):
                print u'"{}" is not a valid directory. Skipping..'.format(self.data_path)
                continue
            if len(glob(os.path.join(self.data_path, '*.torrent'))) > 1:
                print u'Error: Multiple torrent files found in "{}". Skipping..'.format(self.data_path)
                continue
            elif len(glob(os.path.join(self.data_path, '*.torrent'))) < 1:
                print u'Error: No torrent files found in "{}". Skipping..'.format(self.data_path)
                continue
            self.torrent_path = wm_unicode(glob(os.path.join(self.data_path, '*.torrent'))[0])

            with open(wm_str(self.torrent_path), 'rb') as f:
                try:
                    self.torrent_info = bencode.bdecode(f.read())
                    self.info_hash = hashlib.sha1(bencode.bencode(self.torrent_info['info'])).hexdigest().upper()
                except:
                    print u'Invalid torrent file. Skipping..'
                    continue
                self.data_path = os.path.join(self.data_path,
                                            wm_unicode(self.torrent_info['info']['name']))
            print u'Checking to see if torrent is already loaded into WM..'
            masters = list(ReplicaSet.get_what_master().transinstance_set.all())
            try:
                TransTorrent.objects.get(instance__in=masters, info_hash=self.info_hash)
                print u'Torrent already added to WM. Skipping..'
                continue
            except TransTorrent.DoesNotExist:
                pass
            self.what_torrent = WhatTorrent.get_or_create(self.pseudo_request, info_hash=self.info_hash)
            if not self.check_files():
                print u'File check failed. Skipping..'
                continue
            self.move_files()
            print u'Adding torrent to WM...'
            manage_torrent.add_torrent(self.pseudo_request, self.trans_instance,
                                    self.download_location, self.what_torrent.id)
            print u'Done!'
