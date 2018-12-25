
import os.path

from pyquery.pyquery import PyQuery

from qiller.what_api import WHAT_CD_DOMAIN

from qobuz2.settings import QILLER_ERROR_OUTPUT

WHAT_UPLOAD_URL = 'https://{0}/upload.php'.format(WHAT_CD_DOMAIN)
WHAT_RELEASE_TYPES = (
    (1, 'Album'),
    (3, 'Soundtrack'),
    (5, 'EP'),
    (6, 'Anthology'),
    (7, 'Compilation'),
    (8, 'DJ Mix'),
    (9, 'Single'),
    (11, 'Live album'),
    (13, 'Remix'),
    (14, 'Bootleg'),
    (15, 'Interview'),
    (16, 'Mixtape'),
    (21, 'Unknown'),
    (22, 'Concert Recording'),
    (23, 'Demo'),
)


def get_release_type_id(name):
    name = str(name)
    for release_type in WHAT_RELEASE_TYPES:
        if release_type[1] == name:
            return release_type[0]
    return None


def extract_upload_errors(html):
    pq = PyQuery(html)
    result = []
    for e in pq.find('.thin > p[style="color: red; text-align: center;"]'):
        result.append(PyQuery(e).text())
    return result


class MissingImageException(Exception):
    pass


class WhatUploader(object):
    def __init__(self, what_api, temp_dir, metadata):
        self.what_api = what_api
        self.temp_dir = temp_dir
        self.torrent_file_path = os.path.join(temp_dir, metadata.torrent_name + '.torrent')
        self.metadata = metadata

    def _perform_upload(self, payload, payload_files):
        old_content_type = self.what_api.session.headers['Content-type']
        try:
            del self.what_api.session.headers['Content-type']
            response = self.what_api.session.post(WHAT_UPLOAD_URL, data=payload,
                                                  files=payload_files)
            if response.url == WHAT_UPLOAD_URL:
                try:
                    errors = extract_upload_errors(response.text)
                except Exception:
                    errors = ''
                exception = Exception(
                    'Error uploading data to Redacted. Errors: {0}'.format('; '.join(errors)))
                with open(QILLER_ERROR_OUTPUT, 'w') as error_file:
                    error_file.write(response.text.encode('utf-8'))
                raise exception
        finally:
            self.what_api.session.headers['Content-type'] = old_content_type

    def get_release_desc(self):
        lines = []
        if self.metadata.release_description:
            lines.append(self.metadata.release_description)
        if any(hasattr(t, 'spectral_url') for t in self.metadata.tracks):
            if lines:
                lines.append('')
            lines.append('Spectrals:')
            for track in self.metadata.tracks:
                if hasattr(track, 'spectral_url'):
                    lines.append(track.spectral_url)
        return '\n'.join(lines)

    def _upload_in_group(self, group_id, remaster):
        payload_files = dict()
        payload_files['file_input'] = ('torrent.torrent', open(self.torrent_file_path, 'rb'))

        payload = dict()
        payload['submit'] = 'true'
        payload['auth'] = self.what_api.authkey
        payload['type'] = 'Music'
        payload['groupid'] = str(group_id)
        payload['format'] = 'FLAC'
        payload['bitrate'] = 'Lossless'
        payload['media'] = 'WEB'
        payload['release_desc'] = self.get_release_desc()
        if remaster:
            payload['remaster'] = 'on'
            payload['remaster_year'] = remaster['year']
            payload['remaster_title'] = remaster['title']
            payload['remaster_record_label'] = remaster['record_label']
            payload['remaster_catalogue_number'] = remaster['catalogue_number']
        self._perform_upload(payload, payload_files)

    def upload_in_subgroup(self, group_id, with_torrent_id=None):
        if with_torrent_id:
            with_torrent = self.what_api.request('torrent', id=with_torrent_id)['response']
            assert with_torrent['torrent']['remastered']
            self._upload_in_group(group_id, remaster={
                'year': with_torrent['torrent']['remasterYear'],
                'title': with_torrent['torrent']['remasterTitle'],
                'record_label': with_torrent['torrent']['remasterRecordLabel'],
                'catalogue_number': with_torrent['torrent']['remasterCatalogueNumber'],
            })
        else:
            self._upload_in_group(group_id, remaster={
                'year': str(self.metadata.year),
                'title': '',
                'record_label': self.metadata.label,
                'catalogue_number': '',
            })

    def upload_in_original_release(self, group_id):
        self._upload_in_group(group_id, None)

    def check_artists(self):
        for artist in self.metadata.artists:
            try:
                what_artist = self.what_api.request('artist', artistname=artist.name)
                assert what_artist['status'] == 'success'
            except:
                raise Exception('Artist {0} not found on Redacted'.format(artist.name))
            if what_artist['response']['name'] != artist.name:
                raise Exception('Artist {0} is named {1} on Redacted'.format(
                    artist.name, what_artist['response']['name']
                ))

    def upload_new_group(self, release_type_id, tags, title=None, force_artists=False,
                         remaster=False, original_year=None):
        if not force_artists:
            self.check_artists()
        if title is None:
            title = self.metadata.title
        if not tags:
            raise Exception('No tags present')
        if not hasattr(self.metadata, 'image_url'):
            raise MissingImageException('Image URL not found. Upload the cover.')
        if remaster:
            assert original_year, 'You need to specify original year with remaster'
        payload_files = dict()
        payload_files['file_input'] = ('torrent.torrent', open(self.torrent_file_path, 'rb'))

        payload = dict()
        payload['submit'] = 'true'
        payload['auth'] = self.what_api.authkey
        payload['type'] = 'Music'
        payload['artists[]'] = tuple(i.name for i in self.metadata.artists)
        payload['importance[]'] = tuple(i.artist_type for i in self.metadata.artists)
        payload['title'] = title
        if remaster:
            payload['year'] = original_year
            payload['record_label'] = ''
            payload['remaster'] = 'on'
            payload['remaster_year'] = str(self.metadata.year)
            payload['remaster_title'] = ''
            payload['remaster_record_label'] = self.metadata.label
            payload['remaster_catalogue_number'] = ''
        else:
            payload['year'] = str(self.metadata.year)
            payload['record_label'] = self.metadata.label
        payload['releasetype'] = str(release_type_id)
        payload['format'] = 'FLAC'
        payload['bitrate'] = 'Lossless'
        payload['media'] = 'WEB'
        payload['tags'] = tags
        payload['image'] = self.metadata.image_url
        payload['album_desc'] = self.metadata.gen_description()
        payload['release_desc'] = self.get_release_desc()
        self._perform_upload(payload, payload_files)
