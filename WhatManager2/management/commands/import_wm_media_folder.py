from optparse import make_option
from glob import glob
import os
import os.path
import errno
import shutil

import bencode
from django.core.management.base import BaseCommand
from django.db.utils import OperationalError

from WhatManager2 import manage_torrent
from WhatManager2.utils import wm_unicode, wm_str
from home.models import WhatTorrent, DownloadLocation, ReplicaSet, TransTorrent, RequestException
from what_transcode.utils import get_info_hash

def safe_makedirs(p):
    try:
        os.makedirs(wm_str(p))
    except OSError as ex:
        if ex.errno != errno.EEXIST:
            raise ex


class Command(BaseCommand):
    args = '<wm_media>'
    help = u'Scans previous WM media folder and imports available torrents + data'

    def __init__(self):
        super(Command, self).__init__()
        self.pseudo_request = lambda: None
        self.trans_instance = None
        self.download_location = DownloadLocation.get_what_preferred()
        self.data_path = None # folder containing files listed in torrent file
        self.torrent_path = None # path to torrent file
        self.torrent_info = None # torrent data
        self.torrent_id = None # torrent ID
        self.info_hash = None # hash of torrent data
        self.dest_path = None # path where transmission expects files to be
        self.what_torrent = None

    def base_dir(self):
        return os.path.join(self.wm_media, self.torrent_id)

    def subfolder_move(self, subfolder, torrent_id):
        s = wm_str(os.path.join(self.wm_media, torrent_id)) # source
        d = wm_str(os.path.join(self.wm_media, subfolder, torrent_id)) # dest
        safe_makedirs(os.path.dirname(d))
        try:
            shutil.move(s, d)
        except Exception as e:
            shutil.rmtree(d)
            raise e

    def check_args(self, args):
        if len(args) != 1:
            return False
        if not os.path.isdir(args[0]):
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
        try:
            os.makedirs(wm_str(self.dest_path))
            os.chmod(self.dest_path, 0777)
        except:
            print u'Error: Could not create destination directory "{}"'.format(self.dest_path)
            return False
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
        print u'Moving old data directory to "imported" folder..'
        self.subfolder_move('imported', self.torrent_id)  

    def handle(self, *args, **options):
        if not self.check_args(args):
            print u'Pass the directory containing your torrent directories from a previous WM' \
                  u' install. Subfolders of this directory should be named by torrent ID.'
            return

        self.wm_media = wm_unicode(args[0])

        for self.torrent_id in next(os.walk(self.wm_media))[1]:
            try:
                if not os.path.isdir(self.base_dir()):
                    print u'"{}" is not a valid directory. Skipping..'.format(self.base_dir())
                    continue
                torrents = []
                for p in os.listdir(self.base_dir()):
                    if p.endswith('.torrent'):
                        torrents.append(p)
                if len(torrents) > 0:
                    for t in torrents:
                        try:
                            self.torrent_path = os.path.join(self.base_dir(), wm_unicode(torrents[0]))
                            self.info_hash = get_info_hash(self.torrent_path)
                            break
                        except IOError:
                            self.torrent_path = None
                            self.info_hash = None
                            pass
                    if len(torrents) > 1:
                        for t in torrents:
                            try:
                                if get_info_hash(t) != self.info_hash:
                                    print(u'Error: Multiple unique torrent files found. Moving data and skipping..')
                                    self.subfolder_move('multiple_torrent', self.torrent_id)  
                                    torrents = None
                                    break
                            except IOError:
                                continue
                        if torrents == None:
                            continue
                else:
                    if self.torrent_id.isdigit():
                        print u'Error: No torrent files found in "{}". Moving data and skipping..'.format(self.base_dir())
                        self.subfolder_move('no_torrents', self.torrent_id) 
                    continue
            except UnicodeDecodeError as e:
                print u'UnicodeDecodeError: Please import manually. Skipping..'
                continue

            with open(wm_str(self.torrent_path), 'rb') as f:
                try:
                    self.torrent_info = bencode.bdecode(f.read())
                    self.info_hash = get_info_hash(self.torrent_path)
                except:
                    print u'Invalid torrent file. Moving data folder and skipping..'
                    self.subfolder_move('invalid_torrent', self.torrent_id)
                    continue
                self.data_path = os.path.join(self.base_dir(), wm_unicode(self.torrent_info['info']['name']))
            print u'Checking to see if torrent is already loaded into WM..'
            masters = list(ReplicaSet.get_what_master().transinstance_set.all())
            try:
                TransTorrent.objects.get(instance__in=masters, info_hash=self.info_hash)
                print u'Torrent already added to WM. Moving data and skipping..'
                self.subfolder_move('already_added', self.torrent_id)
                continue
            except TransTorrent.DoesNotExist:
                pass
            try:
                self.what_torrent = WhatTorrent.get_or_create(self.pseudo_request, info_hash=self.info_hash)
            except RequestException as e:
                if 'bad hash' in str(e):
                    print u'Bad hash. Torrent may have been trumped/deleted. Moving data folder and skipping import..'.format(str(e))
                    self.subfolder_move('bad_hash', self.torrent_id)
                    continue
                else:
                    raise e
            except OperationalError as e:
                if 'MySQL' in str(e):
                    print u'{}. Please check {} manually. Moving data and skipping..'.format(str(e), self.torrent_id)
                    self.subfolder_move('mysql_error', self.torrent_id)
                    continue
                else:
                    raise e
            if not self.check_files():
                print u'File check failed. Moving data and skipping import..'
                try:
                    self.subfolder_move('file_check_fail', self.torrent_id)
                except UnicodeDecodeError as e:
                    print u'UnicodeDecodeError. Move failed. Please manually check {} Skipping..'.format(self.torrent_id)
                continue
            self.move_files()
            print u'Adding torrent to WM...'
            self.trans_instance = ReplicaSet.get_what_master().get_preferred_instance()
            manage_torrent.add_torrent(self.pseudo_request, self.trans_instance,
                                    self.download_location, self.what_torrent.id)
            print u'Done!'
