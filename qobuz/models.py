from datetime import datetime

from django import forms
from django.core.validators import RegexValidator
from django.db import models

# Create your models here.
from django.template.defaultfilters import title
from django.utils.functional import cached_property
import os.path
import ujson
from WhatManager2.settings import MEDIA_ROOT
from home.models import WhatTorrent


def fix_filepath(path):
    return ''.join(c for c in path if c not in '\/:*?"<>|')


class LoginDataCache(models.Model):
    data_json = models.TextField()

    @cached_property
    def data(self):
        return ujson.loads(self.data_json)


class QobuzUpload(models.Model):
    added = models.DateTimeField(auto_now_add=True)
    qobuz_album_id = models.CharField(max_length=32)
    artists = models.CharField(max_length=256)
    album_name = models.CharField(max_length=256)
    album_year = models.CharField(max_length=7)
    album_data_json = models.TextField()
    track_data_json = models.TextField()
    download_task_id = models.CharField(max_length=64, null=True)
    what_img_cover = models.CharField(max_length=256, null=True)
    what_torrent = models.ForeignKey(WhatTorrent, null=True, on_delete=models.CASCADE)

    @cached_property
    def description_box(self):
        lines = []
        lines.append('{0} - {1} ({2})'.format(self.artists, self.album_name, self.album_year))
        lines.append('Label: {0}'.format(self.album_data['label']['name']))
        lines.append('Genre: {0}'.format(
            self.album_data['genre']['name']))
        lines.append('')
        track_number = 0
        media_number = 0
        for i, track in enumerate(self.album_data['tracks']['items']):
            if track['media_number'] != media_number:
                track_number = 1
                media_number = track['media_number']
            if self.album_data['tracks']['items'][-1]['media_number'] > 1:
                prefix = '{0}.{1:02}'.format(media_number, track_number)
            else:
                prefix = '{0:02}'.format(track_number)
            lines.append('{0}. {1} ({2}:{3:02})'.format(
                prefix, self.track_data[i]['title'],
                int(track['duration']) // 60,
                int(track['duration']) % 60
            ))
            track_number += 1
        return '\n'.join(lines)

    def populate_fields(self):
        self.artists = self.album_data['artist']['name']
        self.album_name = title(self.album_data['title'])
        self.album_year = datetime.utcfromtimestamp(self.album_data['released_at']).year
        track_data = []
        for track in self.album_data['tracks']['items']:
            track_data.append({
                'media_number': track['media_number'],
                'artists': track['performer']['name'],
                'title': title(track['title']),
            })
        self.track_data_json = ujson.dumps(track_data)

    @cached_property
    def torrent_name(self):
        return '{0} - {1} - {2} (WEB - FLAC - Lossless)'.format(
            fix_filepath(self.artists),
            fix_filepath(self.album_name),
            fix_filepath(self.album_year)
        )

    @cached_property
    def temp_media_path(self):
        return os.path.join(MEDIA_ROOT, 'qobuz_uploads', self.torrent_name)

    @cached_property
    def album_data(self):
        return ujson.loads(self.album_data_json)

    @cached_property
    def track_data(self):
        return ujson.loads(self.track_data_json)

    @cached_property
    def spectrals_path(self):
        return os.path.join(self.temp_media_path, 'spectrals')


class NewUploadForm(forms.Form):
    album_id = forms.CharField(max_length=32, validators=[RegexValidator('^[0-9]+$')])


class EditUploadForm(forms.Form):
    artists = forms.CharField(max_length=256)
    album_name = forms.CharField(max_length=256)
    album_year = forms.CharField(max_length=7)
    what_img_cover = forms.CharField(required=False)

    def __init__(self, *args, **kwargs):
        qobuz_upload = kwargs.pop('qobuz_upload')
        initial = {
            'artists': qobuz_upload.artists,
            'album_name': qobuz_upload.album_name,
            'album_year': qobuz_upload.album_year,
            'what_img_cover': qobuz_upload.what_img_cover,
        }
        for i, track in enumerate(qobuz_upload.track_data):
            media_number = qobuz_upload.album_data['tracks']['items'][i]['media_number']
            title_field = 'track_{0}_{1}_title'.format(media_number, i + 1)
            artists_field = 'track_{0}_{1}_artists'.format(media_number, i + 1)
            initial[title_field] = track['title']
            initial[artists_field] = track['artists']
        kwargs['initial'] = initial
        super(EditUploadForm, self).__init__(*args, **kwargs)
        for i, track in enumerate(qobuz_upload.track_data):
            media_number = qobuz_upload.album_data['tracks']['items'][i]['media_number']
            title_field = 'track_{0}_{1}_title'.format(media_number, i + 1)
            artists_field = 'track_{0}_{1}_artists'.format(media_number, i + 1)
            self.fields[title_field] = forms.CharField()
            self.fields[artists_field] = forms.CharField()
