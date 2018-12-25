
import logging
import os.path
import shutil

from mutagen.flac import FLAC


logger = logging.getLogger(__name__)


def conditional_rename(src, dst):
    if src != dst:
        logger.debug('Renaming {0} to {1}'.format(src, dst))
        shutil.move(src, dst)


class Preparer(object):
    def __init__(self, temp_dir):
        self.temp_dir = temp_dir

    def prepare_goodie(self, goodie):
        src = os.path.join(self.temp_dir, goodie.temp_filename)
        dst = os.path.join(self.temp_dir, goodie.filename)
        conditional_rename(src, dst)

    def prepare_image(self, image):
        src = os.path.join(self.temp_dir, image.temp_filename)
        dst = os.path.join(self.temp_dir, image.filename)
        conditional_rename(src, dst)

    def prepare_track(self, album, track):
        temp_path = os.path.join(self.temp_dir, track.temp_filename)
        track_path = os.path.join(self.temp_dir, track.filename)
        meta_file = FLAC(temp_path)
        meta_file.clear()
        meta_file['album'] = album.title
        meta_file['albumartist'] = album.joined_artists
        meta_file['artist'] = track.joined_artists
        meta_file['title'] = track.title
        meta_file['date'] = str(album.year)
        meta_file['genre'] = album.genre
        meta_file['tracknumber'] = str(track.track_number)
        meta_file['totaltracks'] = str(track.track_total)
        meta_file['discnumber'] = str(track.media_number)
        meta_file['totaldiscs'] = str(album.media_total)
        meta_file.save()
        conditional_rename(temp_path, track_path)
