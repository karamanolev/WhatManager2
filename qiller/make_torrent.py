
import logging
import os
from subprocess import call

import os.path

from what_transcode.utils import pthify_torrent

BAD_FILES = ['.ds_store', 'thumbs.db']

logger = logging.getLogger(__name__)


def remove_bad_files(temp_dir):
    for f in os.listdir(temp_dir):
        if f.lower() in BAD_FILES:
            os.remove(os.path.join(temp_dir, f))
            logger.info('{0} file found. Removing.'.format(f))
            os.remove(os.path.join(temp_dir, f))


class TorrentMaker(object):
    def __init__(self, temp_dir, stash_func, unstash_func, announce):
        self.temp_dir = temp_dir
        self.stash_func = stash_func
        self.unstash_func = unstash_func
        self.announce = announce

    def make_torrent(self, metadata):
        try:
            self.stash_func()
            remove_bad_files(self.temp_dir)
            torrent_path = os.path.join(self.temp_dir, metadata.torrent_name + '.torrent')
            args = [
                'mktorrent',
                '-a', self.announce,
                '-p',
                '-n', metadata.torrent_name,
                '-o', torrent_path,
                self.temp_dir
            ]
            logger.debug('Executing mktorrent: {0}'.format(args))
            if call([a for a in args]) != 0:
                raise Exception('mktorrent returned non-zero')
            with open(torrent_path, 'rb') as f:
                torrent_data = f.read()
            torrent_data = pthify_torrent(torrent_data)
            with open(torrent_path, 'wb') as f:
                f.write(torrent_data)
        finally:
            self.unstash_func()
