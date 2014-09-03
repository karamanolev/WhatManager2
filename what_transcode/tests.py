"""
This file demonstrates writing tests using the unittest module. These will pass
when you run "manage.py test".

Replace this with more appropriate tests for your application.
"""

from django.test import TestCase

from what_transcode.utils import get_mp3_ids


class UtilsTests(TestCase):
    def test_get_mp3_ids(self):
        what_group = {
            'torrents': [
                {
                    'id': 0,
                    'format': 'FLAC',
                    'encoding': 'Lossless',
                    'media': 'CD',
                    'remastered': False,
                    'remasterCatalogueNumber': None,
                    'remasterRecordLabel': None,
                    'remasterTitle': None,
                    'remasterYear': None,
                },
                {
                    'id': 1,
                    'format': 'MP3',
                    'encoding': '320',
                    'media': 'CD',
                    'remastered': False,
                    'remasterCatalogueNumber': None,
                    'remasterRecordLabel': None,
                    'remasterTitle': None,
                    'remasterYear': None,
                },
                {
                    'id': 2,
                    'format': 'FLAC',
                    'encoding': 'Lossless',
                    'media': 'CD',
                    'remastered': True,
                    'remasterCatalogueNumber': 'catno',
                    'remasterRecordLabel': None,
                    'remasterTitle': None,
                    'remasterYear': None,
                },
                {
                    'id': 3,
                    'format': 'FLAC',
                    'encoding': 'Lossless',
                    'media': 'WEB',
                    'remastered': False,
                    'remasterCatalogueNumber': None,
                    'remasterRecordLabel': None,
                    'remasterTitle': None,
                    'remasterYear': None,
                },
                {
                    'id': 4,
                    'format': 'MP3',
                    'encoding': 'V0 (VBR)',
                    'media': 'WEB',
                    'remastered': False,
                    'remasterCatalogueNumber': None,
                    'remasterRecordLabel': None,
                    'remasterTitle': None,
                    'remasterYear': None,
                },
                {
                    'id': 5,
                    'format': 'MP3',
                    'encoding': 'V2 (VBR)',
                    'media': 'WEB',
                    'remastered': False,
                    'remasterCatalogueNumber': None,
                    'remasterRecordLabel': None,
                    'remasterTitle': None,
                    'remasterYear': None,
                },
            ]
        }
        self.assertEqual(get_mp3_ids(what_group, {
            'torrent': what_group['torrents'][0]
        }), {'320': 1})
        self.assertEqual(get_mp3_ids(what_group, {
            'torrent': what_group['torrents'][2]
        }), {})
        self.assertEqual(get_mp3_ids(what_group, {
            'torrent': what_group['torrents'][3]
        }), {'V0': 4, 'V2': 5})
