
import logging
import os
import os.path
import shutil
from subprocess import call

from PIL import Image
import imgurpython

from qiller.utils import time_text, ensure_file_dir_exists, retry_action


logger = logging.getLogger(__name__)


class SpectralManager(object):
    def __init__(self, temp_dir, high_color):
        self.temp_dir = temp_dir
        self.high_color = high_color
        self.spectrals_dir = os.path.join(self.temp_dir, 'spectrals')

    @property
    def stash_dir(self):
        pid = os.getpid()
        return os.path.join(os.path.dirname(self.temp_dir), 'spectrals.{0}'.format(pid))

    def stash(self):
        shutil.move(self.spectrals_dir, self.stash_dir)

    def unstash(self):
        shutil.move(self.stash_dir, self.spectrals_dir)

    def get_filenames(self, track):
        basename = os.path.splitext(track.filename)[0]
        return (
            (
                os.path.join(self.spectrals_dir, '{0}.full.png'.format(basename)),
                os.path.join(self.spectrals_dir, '{0}.zoom.png'.format(basename)),
            ),
            os.path.join(self.spectrals_dir, '{0}.png'.format(basename))
        )

    def _generate_temp_spectral(self, track, filenames):
        assert len(filenames) == 2
        track_path = os.path.join(self.temp_dir, track.temp_filename)
        logger.info('Generating spectrals for {0}'.format(track.temp_filename))
        full_title = '{0} Full'.format(os.path.splitext(track.filename)[0])
        zoom_title = '{0} Zoom'.format(os.path.splitext(track.filename)[0])
        ensure_file_dir_exists(filenames[0])
        ensure_file_dir_exists(filenames[0])
        args = [
            'sox', track_path, '-n', 'remix', '1', 'spectrogram', '-x', '3000', '-y', '513', '-w',
            'Kaiser', '-t', full_title, '-o', filenames[0]
        ]
        if self.high_color:
            args.append('-h')
        if call([a for a in args]) != 0:
            raise Exception('sox returned non-zero')
        assert track.duration >= 4, 'Track is shorter than 4 seconds'
        zoom_start = time_text(min(40, track.duration - 4))
        args = [
            'sox', track_path, '-n', 'remix', '1', 'spectrogram', '-x', '3000', '-y', '513', '-w',
            'Kaiser', '-S', zoom_start, '-d', '0:04', '-t', zoom_title, '-o', filenames[1]
        ]
        if self.high_color:
            args.append('-h')
        if call([a for a in args]) != 0:
            raise Exception('sox returned non-zero')

    def generate_spectral(self, track):
        filenames = self.get_filenames(track)
        self._generate_temp_spectral(track, filenames[0])
        self._merge_spectrals(filenames[0], filenames[1])
        for temp_spectral in filenames[0]:
            os.remove(temp_spectral)


    @staticmethod
    def _merge_spectrals(paths, dest_path):
        images = list(map(Image.open, [p for p in paths]))
        try:
            result_width = max(i.size[0] for i in images)
            result_height = sum(i.size[1] for i in images)
            result = Image.new('P', (result_width, result_height))
            result.putpalette(images[0].getpalette())
            current_y = 0
            for image in images:
                result.paste(image, (0, current_y, image.size[0], current_y + image.size[1]))
                current_y += image.size[1]
            result.save(dest_path, 'PNG')
        finally:
            for image in images:
                image.close()


class SpectralUploader(object):
    def __init__(self, temp_dir, imgur_client_id):
        self.manager = SpectralManager(temp_dir, False)
        self.imgur_client = imgurpython.ImgurClient(imgur_client_id, '')

    def upload_spectral(self, track):
        if hasattr(track, 'spectral_url'):
            return track.spectral_url
        spectral_path = self.manager.get_filenames(track)[1]
        resp = []

        def do_upload():
            resp.append(self.imgur_client.upload_from_path(spectral_path))

        retry_action(do_upload)
        track.spectral_url = resp[0]['link']
        return track.spectral_url
