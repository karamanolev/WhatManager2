import functools
import multiprocessing.dummy as multiprocessing
import pickle
import shutil
import os.path

from requests.exceptions import HTTPError

from qiller import whatimg
from qiller.download import Downloader
from qiller.make_torrent import TorrentMaker
from qiller.metadata import UploadMetadata
from qiller.prepare import Preparer
from qiller.spectrals import SpectralManager, SpectralUploader
from qiller.utils import FLACTester, download_test_spectral
from qiller.what_upload import WhatUploader


class QillerUpload(object):
    DEFAULT_CONCURRENCY = 2

    STATE_INITIALIZED = 1
    STATE_DOWNLOADED = 2
    STATE_PREPARED = 3
    STATE_TORRENT_CREATED = 4
    STATE_UPLOADED_WHAT = 5

    def __init__(self, temp_dir):
        if os.path.exists(temp_dir):
            raise Exception('Destination directory already exists. Run clean.')
        self.concurrency = self.DEFAULT_CONCURRENCY
        self.metadata = None
        self.state = None

    def load_from_qobuz(self, qobuz_api, temp_dir, album_id):
        try:
            qobuz_album = qobuz_api.call('album/get', album_id=album_id)
        except HTTPError:
            raise Exception('Couldn\'t fetch Qobuz album.')
        self.metadata = UploadMetadata()
        self.metadata.load_from_qobuz(qobuz_api, qobuz_album)
        self.state = self.STATE_INITIALIZED
        os.mkdir(temp_dir)

    def load_from_tidal(self, tidal_api, temp_dir, album_id):
        self.concurrency = 4
        try:
            tidal_album = tidal_api.call('albums', album_id)
            tidal_tracks = tidal_api.call('albums', album_id, 'tracks')
        except HTTPError:
            raise Exception('Couldn\'t fetch Qobuz album.')
        self.metadata = UploadMetadata()
        self.metadata.load_from_tidal(tidal_api, tidal_album, tidal_tracks)
        self.state = self.STATE_INITIALIZED
        os.mkdir(temp_dir)

    def download(self, temp_dir, high_color_spectrals):
        assert self.state == self.STATE_INITIALIZED, 'Can\'t download in current state'
        downloader = Downloader(temp_dir)
        tester = FLACTester(temp_dir)
        spectrals = SpectralManager(temp_dir, high_color_spectrals)
        download_track = functools.partial(download_test_spectral, downloader, tester, spectrals)
        pool = multiprocessing.Pool(self.concurrency)
        pool.map(downloader.download_goodie, self.metadata.goodies)
        pool.map(downloader.download_image, self.metadata.images)
        pool.map(download_track, self.metadata.tracks)
        pool.close()
        pool.join()
        self.state = self.STATE_DOWNLOADED

    def clean(self, temp_dir):
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)
        self.state = self.STATE_INITIALIZED

    def prepare(self, temp_dir):
        assert self.state == self.STATE_DOWNLOADED, 'Can\'t prepare in current state'
        preparer = Preparer(temp_dir)
        list(map(preparer.prepare_goodie, self.metadata.goodies))
        list(map(preparer.prepare_image, self.metadata.images))
        list(map(functools.partial(preparer.prepare_track, self.metadata), self.metadata.tracks))
        self.state = self.STATE_PREPARED

    def make_torrent(self, temp_dir, announce):
        assert self.state == self.STATE_PREPARED, 'Can\'t make torrent in current state'
        spectrals = SpectralManager(temp_dir, False)
        maker = TorrentMaker(temp_dir, spectrals.stash, spectrals.unstash, announce)
        maker.make_torrent(self.metadata)
        self.state = self.STATE_TORRENT_CREATED

    def upload_to_what(self, what_api, temp_dir, method, args=None, kwargs=None):
        if args is None:
            args = []
        if kwargs is None:
            kwargs = {}
        assert self.state == self.STATE_TORRENT_CREATED, 'Can\'t upload in current state'
        uploader = WhatUploader(what_api, temp_dir, self.metadata)
        getattr(uploader, method)(*args, **kwargs)
        self.state = self.STATE_UPLOADED_WHAT

    def upload_cover(self, temp_dir, username, password, album_id):
        if hasattr(self.metadata, 'image_url'):
            raise Exception('Image already uploaded to {0}'.format(self.metadata.image_url))
        for image in self.metadata.images:
            if image.name == 'large':
                with open(os.path.join(temp_dir, image.filename), 'rb') as f:
                    url = whatimg.upload_image_from_memory(username, password, album_id, f.read())
                    self.metadata.image_url = url
                    return
        raise Exception('Qobuz large image not found for uploading')

    def upload_spectrals(self, temp_dir, imgur_client_id):
        uploader = SpectralUploader(temp_dir, imgur_client_id)
        for track in self.metadata.tracks:
            uploader.upload_spectral(track)

    @classmethod
    def save(cls, upload):
        return pickle.dumps(upload)

    @classmethod
    def load(cls, saved):
        return pickle.loads(saved)

    @classmethod
    def save_file(cls, path, upload):
        with open(path, 'wb') as f:
            f.write(cls.save(upload))

    @classmethod
    def load_file(cls, path):
        with open(path, 'rb') as f:
            return cls.load(f.read())
