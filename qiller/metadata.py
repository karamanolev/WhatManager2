
from datetime import datetime

from qiller.utils import strip_path_chars, time_text, extract_label


WHAT_ARTIST_TYPES = {
    1: 'Main',
    2: 'Guest',
    4: 'Composer',
    5: 'Conductor',
    6: 'DJ / Compiler',
    3: 'Remixer',
    7: 'Producer',
}


def fix_qobuz_artist_name(name):
    assert type(name) is str
    name = name.replace('Interpr\xe8tes Divers', 'Various Artists')
    return name


class UploadArtist(object):
    def __init__(self, name, artist_type):
        """
        Creates an UploadArtist that will be used when submitting to What.CD
        name -- the name of the artist
        artist_type -- an integer [1, 7] per WHAT_ARTIST_TYPES
        """
        assert type(artist_type) is int
        self.name = name
        self.artist_type = artist_type


class TrackMetadata(object):
    def __init__(self, upload):
        self.upload = upload
        self.id = None
        self.url = None
        self.joined_artists = None
        self.title = None
        self.track_number = None
        self.track_total = None
        self.media_number = None
        self.duration = None

    def load_from_qobuz(self, download_url, track_total, track_data):
        assert track_data['streamable'], 'Album contains unstreamable tracks'
        self.id = track_data['id']
        self.url = download_url
        if 'performer' in track_data:
            self.joined_artists = fix_qobuz_artist_name(track_data['performer']['name'])
        elif 'performers' in track_data:
            self.joined_artists = fix_qobuz_artist_name(track_data['performers'])
        else:
            raise Exception('Neither performer nor performers on track')
        self.title = track_data['title']
        self.track_number = track_data['track_number']
        self.track_total = track_total
        self.media_number = track_data['media_number']
        self.duration = int(track_data['duration'])

    def load_from_tidal(self, download_url, track_total, track_data):
        self.id = track_data['id']
        self.url = download_url
        self.joined_artists = track_data['artist']['name']
        self.title = track_data['title']
        if track_data.get('version'):
            if not self.title.strip(' ()').endswith(track_data['version'].strip(' ()')):
                self.title += ' ({0})'.format(track_data['version'])
        self.track_number = track_data['trackNumber']
        self.track_total = track_total
        self.media_number = track_data['volumeNumber']
        self.duration = int(track_data['duration'])

    @property
    def temp_filename(self):
        return '{0}.flac'.format(self.id)

    @property
    def filename(self):
        assert self.track_number < 100, 'With more than 100 tracks this will break ordering'
        data_dict = dict(self.__dict__)
        if self.upload.various_artists_mode:
            data_dict['fname'] = '{0} - {1}'.format(self.joined_artists, self.title)
        else:
            data_dict['fname'] = self.title
        if self.upload.media_total > 10:
            name = '{media_number:02d}.{track_number:02d}. {fname}.flac'.format(**data_dict)
        elif self.upload.media_total > 1:
            name = '{media_number}.{track_number:02d}. {fname}.flac'.format(**data_dict)
        else:
            name = '{track_number:02d}. {fname}.flac'.format(**data_dict)
        return strip_path_chars(name)

    @property
    def duration_text(self):
        return time_text(self.duration)


class GoodieMetadata(object):
    def __init__(self):
        self.id = None
        self.name = None
        self.url = None

    def load_from_qobuz(self, goodie_data):
        assert goodie_data['file_format_id'] == 21, 'Only PDF goodies are supported right now'
        assert goodie_data['original_url'].endswith('.pdf')
        self.id = goodie_data['id']
        self.name = goodie_data['description']
        self.url = goodie_data['original_url']

    @property
    def extension(self):
        return 'pdf'

    @property
    def temp_filename(self):
        return '{0}.{1}'.format(self.id, self.extension)

    @property
    def filename(self):
        return strip_path_chars('{0}.{1}'.format(self.name, self.extension))


def fix_qobuz_image_url(url):
    suffix = url[-8:]
    assert suffix in ('_230.jpg', '_600.jpg'), 'Weird image url'
    return url[:-8] + '_600.jpg'


class ImageMetadata(object):
    def __init__(self, name, url):
        self.name = name
        self.url = url

    @property
    def temp_filename(self):
        return self.filename

    @property
    def filename(self):
        if self.name == 'large':
            return 'folder.jpg'
        elif self.name == 'back':
            return 'back.jpg'
        else:
            raise Exception('Unknown image type: {0}'.format(self.name))


class UploadMetadata(object):
    def __init__(self):
        self.id = None
        self.joined_artists = None
        self.artists = None
        self.title = None
        self.year = None
        self.label = None
        self.genre = None
        self.tracks = None
        self.images = None
        self.goodies = None
        self.release_description = None
        self.various_artists_mode = None

    def load_from_tidal(self, tidal_api, tidal_album, tidal_tracks):
        self.id = tidal_album['id']
        self.joined_artists = tidal_album['artist']['name']
        self.various_artists_mode = self.joined_artists == 'Various Artists'
        if self.various_artists_mode:
            self.artists = [
                UploadArtist(n, 1) for n in
                {t['artist']['name'] for t in tidal_tracks['items']}
            ]
        else:
            self.artists = [UploadArtist(self.joined_artists, 1)]
        self.title = tidal_album['title']
        assert len(tidal_album['releaseDate']) == 10
        self.year = tidal_album['releaseDate'][:4]
        self.label = extract_label(tidal_album['copyright'])
        self.genre = ''
        self.goodies = []
        self.images = []
        self.images.append(ImageMetadata(
            'large', 'http://resources.wimpmusic.com/images/{0}/{1}x{2}.jpg'.format(
                tidal_album['cover'].replace('-', '/'), 1280, 1280
            )))
        self.tracks = []
        items = sorted(tidal_tracks['items'], key=lambda i: (i['volumeNumber'], i['trackNumber']))
        for track_data in items:
            track = TrackMetadata(self)
            stream_url = tidal_api.call('tracks', str(track_data['id']), 'streamUrl')
            assert stream_url['soundQuality'] == 'LOSSLESS'
            track_total = sum(t['volumeNumber'] == track_data['volumeNumber'] for t in items)
            assert sorted(t['trackNumber'] for t in items if
                          t['volumeNumber'] == track_data['volumeNumber']) == \
                   list(range(1, track_total + 1))
            track.load_from_tidal(stream_url['url'], track_total, track_data)
            self.tracks.append(track)
        # self.release_description = \
        # 'Created from Tidal album http://listen.tidalhifi.com/album/{0}'.format(self.id)
        self.release_description = ''

    def load_from_qobuz(self, qobuz_api, album_data):
        self.id = album_data['id']
        self.joined_artists = fix_qobuz_artist_name(album_data['artist']['name'])
        self.various_artists_mode = self.joined_artists == 'Various Artists'
        self.artists = [UploadArtist(self.joined_artists, 1)]
        self.title = album_data['title']
        self.year = datetime.utcfromtimestamp(album_data['released_at']).year
        self.label = album_data['label']['name']
        self.genre = album_data['genre']['name']
        if 'store_related' in album_data:
            if 'GB-en' in album_data['store_related']:
                if 'genre' in album_data['store_related']['GB-en']:
                    if 'name' in album_data['store_related']['GB-en']['genre']:
                        self.genre = album_data['store_related']['GB-en']['genre']['name']
        self.tracks = []
        self.images = []
        self.goodies = []

        items = album_data['tracks']['items']
        for track_data in items:
            download_info = qobuz_api.get_file_url(track_data['id'])
            assert download_info['mime_type'] == 'audio/flac', 'Track mime type is not audio/flac'
            track_total = sum(t['media_number'] == track_data['media_number'] for t in items)
            assert sorted(t['track_number'] for t in items if
                          t['media_number'] == track_data['media_number']) == \
                   list(range(1, track_total + 1))
            track = TrackMetadata(self)
            track.load_from_qobuz(download_info['url'], track_total, track_data)
            self.tracks.append(track)
        large_url = album_data['image']['large']
        if large_url != 'http://static.qobuz.com/img/common/default_cover_600.png':
            self.images.append(ImageMetadata('large', fix_qobuz_image_url(large_url)))
        back_image = album_data['image']['back']
        if back_image:
            self.image.append(ImageMetadata('back', fix_qobuz_image_url(back_image)))
        if 'goodies' in album_data:
            for goodie_data in album_data['goodies']:
                goodie = GoodieMetadata()
                goodie.load_from_qobuz(goodie_data)
                self.goodies.append(goodie)
        self.release_description = \
            'Created from Qobuz album http://www.qobuz.com/album/name/{0}'.format(self.id)

    @property
    def media_total(self):
        return max(t.media_number for t in self.tracks)

    @property
    def torrent_name(self):
        return '{0} - {1} - {2} (WEB - FLAC)'.format(
            strip_path_chars(self.joined_artists),
            strip_path_chars(self.title),
            strip_path_chars(str(self.year))
        )

    @property
    def duration_text(self):
        return time_text(sum(t.duration for t in self.tracks))

    def gen_description(self):
        lines = []
        lines.append('{0} - {1} ({2})'.format(self.joined_artists, self.title, self.year))
        if self.label:
            lines.append('Label: {0}'.format(self.label))
        if self.genre:
            lines.append('Genre: {0}'.format(self.genre))
        lines.append('Duration: {0}'.format(self.duration_text))
        lines.append('')
        for track in self.tracks:
            if self.media_total > 1:
                prefix = '{0}.{1:02}'.format(track.media_number, track.track_number)
            else:
                prefix = '{0:02}'.format(track.track_number)
            if self.various_artists_mode:
                track_title = '{0} - {1}'.format(track.joined_artists, track.title)
            else:
                track_title = track.title
            lines.append('{0}. {1} ({2})'.format(prefix, track_title, track.duration_text))
        return '\n'.join(lines)
