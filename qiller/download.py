
from contextlib import closing
import logging
import os
import os.path

import requests

from qiller.utils import ensure_file_dir_exists, retry_action


logger = logging.getLogger(__name__)


def stream_download(destination, response):
    ensure_file_dir_exists(destination)
    with open(destination, 'wb') as f:
        for chunk in response.iter_content(4096):
            f.write(chunk)


def stream_reconstruct_download(destination, url):
    session = requests.Session()
    session.headers.update({
        'Accept': '*/*',
        'Origin': 'http://listen.tidalhifi.com',
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/38.0.2125.104 Safari/537.36',
    })
    response = session.options(url)
    assert response.status_code == 200, 'OPTIONS did not return 200'
    offset = 0
    length = 4 * 2 ** 32  # 4MB chunks
    with open(destination, 'wb') as f:
        while offset < length:
            with closing(session.get(url, stream=True, headers={
                'Range': 'bytes={0}-{1}'.format(offset, offset + 2 ** 20 - 1),
            })) as response:
                assert response.status_code == 206, 'GET piece did not return 206'
                length = int(response.headers['Content-Range'].split('/')[1])
                offset += int(response.headers['Content-Length'])
                for chunk in response.iter_content(4096):
                    f.write(chunk)


class Downloader(object):
    def __init__(self, temp_dir):
        if not os.path.exists(temp_dir):
            raise Exception('Destination directory does not exist.')
        self.temp_dir = temp_dir

    def download_goodie(self, goodie):
        def action():
            goodie_path = os.path.join(self.temp_dir, goodie.temp_filename)
            logger.info('Downloading {0}'.format(goodie.url))
            with closing(requests.get(goodie.url, stream=True)) as response:
                assert response.headers['Content-Type'] == 'application/{0}'.format(
                    goodie.extension), \
                    'Wrong goodie Content-Type: {0}'.format(response.headers['Content-Type'])
                stream_download(goodie_path, response)

        retry_action(action)

    def download_image(self, image):
        def action():
            image_path = os.path.join(self.temp_dir, image.temp_filename)
            logger.info('Downloading {0}'.format(image.url))
            with closing(requests.get(image.url, stream=True)) as response:
                assert response.headers['Content-Type'] == 'image/jpeg', \
                    'Wrong image Content-Type: {0}'.format(response.headers['Content-Type'])
                stream_download(image_path, response)

        retry_action(action)

    def download_track(self, track):
        def action():
            track_path = os.path.join(self.temp_dir, track.temp_filename)
            logger.debug('Getting track {0} download URL'.format(track.id))
            logger.info('Downloading {0}'.format(track.url))
            if 'wimpmusic' in track.url or 'compute-1.amazonaws.com' in track.url:
                stream_reconstruct_download(track_path, track.url)
            else:
                with closing(requests.get(track.url, stream=True)) as response:
                    assert response.headers['Content-Type'] == 'audio/flac', \
                        'Wrong track Content-Type: {0}'.format(response.headers['Content-Type'])
                    stream_download(track_path, response)

        retry_action(action)
