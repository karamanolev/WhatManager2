from django.test import TestCase

from what_meta.filtering import sort_filter_torrents


class SimpleTest(TestCase):
    def test_sort_mp3(self):
        torrents = [
            {'format': 'MP3', 'media': 'CD'},
            {'format': 'FLAC', 'media': 'CD'},
            {'format': 'MP3', 'media': 'WEB'},
            {'format': 'MP3', 'media': 'Vinyl'},
        ]
        self.assertEqual(sort_filter_torrents(torrents), [
            torrents[2], torrents[0], torrents[3]
        ])
