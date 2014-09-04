"""
This file demonstrates writing tests using the unittest module. These will pass
when you run "manage.py test".

Replace this with more appropriate tests for your application.
"""

from django.test import TestCase
from WhatManager2.management.commands import transmission_provision

from home.models import WhatTorrent, ReplicaSet


class InfoHolderTest(TestCase):
    fixtures = ['what_torrent_4795.json']

    def test_from_db(self):
        torrent = WhatTorrent.objects.get(id=4795)
        self.assertEqual(torrent.info_artist, 'Various Artists')
        self.assertEqual(torrent.info_remastered, True)
        self.assertEqual(torrent.info_release_type_name, 'Soundtrack')
        self.assertEqual(torrent.info_year, 2007)
        self.assertEqual(torrent.info_title, 'Across the Universe')
        self.assertEqual(torrent.info_media, 'CD')
        self.assertEqual(torrent.info_format, 'FLAC')
        self.assertEqual(torrent.info_encoding, 'Lossless')
        self.assertEqual(torrent.info_label, '')
        self.assertEqual(torrent.info_catno, '')
        self.assertEqual(torrent.info_remaster_title, 'Deluxe Edition')
        self.assertEqual(torrent.info_files, [
            {'name': 'Disc 1/01 - Jim Sturgess - Girl.flac', 'size': 5151005},
            {'name': 'Disc 1/02 - Evan Rachel Wood - Hold Me Tight.flac', 'size': 18990297},
            {'name': 'Disc 1/03 - Jim Sturgess - All My Loving.flac', 'size': 15837235},
            {'name': 'Disc 1/04 - T.V. Carpio - I Want To Hold Your Hand.flac', 'size': 16195916},
            {'name': 'Disc 1/05 - Joe Anderson & Jim Sturgess - With A Little Help From '
                     'My Friends.flac', 'size': 20969167},
            {'name': 'Disc 1/06 - Evan Rachel Wood - It Won\'t Be Long.flac', 'size': 16340862},
            {'name': 'Disc 1/07 - Jim Sturgess - I\'ve Just Seen A Face.flac', 'size': 11360829},
            {'name': 'Disc 1/08 - Carol Woods & Timothy T. Mitchum - Let It Be.flac',
             'size': 21598210},
            {'name': 'Disc 1/09 - Joe Cocker - Come Together.flac', 'size': 29464915},
            {'name': 'Disc 1/10 - Dana Fuchs - Why Don\'t We Do It In The Road .flac',
             'size': 10095996},
            {'name': 'Disc 1/11 - Evan Rachel Wood - If I Fell.flac', 'size': 13500632},
            {'name': 'Disc 1/12 - Joe Anderson, Dana Fuchs & T.V. Carpio - I Want You'
                     ' (She\'s So Heavy).flac', 'size': 23177583},
            {'name': 'Disc 1/13 - Dana Fuchs, Jim Sturgess, Evan Rachel Wood & T.V. Carpio '
                     '- Dear Prudence.flac', 'size': 33351179},
            {'name': 'Disc 1/14 - Secret Machines - Flying.flac', 'size': 26745728},
            {'name': 'Disc 1/15 - Secret Machines - Blue Jay Way.flac', 'size': 29804984},
            {'name': 'Disc 1/Across The Universe (Deluxe Edition) (Disc 1).CUE', 'size': 2998},
            {'name': 'Disc 1/Across The Universe (Deluxe Edition) (Disc 1).log', 'size': 5433},
            {'name': 'Disc 1/Various Artists - Across The Universe (Deluxe Edition) (Disc 1).m3u',
             'size': 1573},
            {'name': 'Disc 2/01 - Bono & Secret Machines - I Am The Walrus.flac', 'size': 32104586},
            {'name': 'Disc 2/02 - Eddie Izzard - Being For The Benefit Of Mr. Kite.flac',
             'size': 17934844},
            {'name': 'Disc 2/03 - Evan Rachel Wood, Jim Sturgess, Joe Anderson, Dana Fuchs, T.V. '
                     'Carpio & Martin Luther McCoy - Because.flac', 'size': 16319333},
            {'name': 'Disc 2/04 - Jim Sturgess - Something.flac', 'size': 17796269},
            {'name': 'Disc 2/05 - Dana Fuchs & Martin Luther McCoy - Oh! Darling.flac',
             'size': 16887109},
            {'name': 'Disc 2/06 - Jim Sturgess & Joe Anderson - Strawberry Fields Forever.flac',
             'size': 24950947},
            {'name': 'Disc 2/07 - Jim Sturgess - Revolution.flac', 'size': 15191872},
            {'name': 'Disc 2/08 - Martin Luther McCoy - While My Guitar Gently Weeps.flac',
             'size': 23498352},
            {'name': 'Disc 2/09 - Jim Sturgess - Across The Universe.flac', 'size': 21964979},
            {'name': 'Disc 2/10 - Dana Fuchs - Helter Skelter.flac', 'size': 26439626},
            {'name': 'Disc 2/11 - Joe Anderson & Salma Hayek - Happiness Is A Warm Gun.flac',
             'size': 20035535},
            {'name': 'Disc 2/12 - Evan Rachel Wood - Blackbird.flac', 'size': 16083658},
            {'name': 'Disc 2/13 - Joe Anderson - Hey Jude.flac', 'size': 26827656},
            {'name': 'Disc 2/14 - Dana Fuchs - Don\'t Let Me Down.flac', 'size': 22103447},
            {'name': 'Disc 2/15 - Jim Sturgess & Dana Fuchs - All You Need Is Love.flac',
             'size': 20833355},
            {'name': 'Disc 2/16 - Bono & The Edge - Lucy In The Sky With Diamonds.flac',
             'size': 28387973},
            {'name': 'Disc 2/Across The Universe (Deluxe Edition) (Disc 2).CUE', 'size': 3306},
            {'name': 'Disc 2/Across The Universe (Deluxe Edition) (Disc 2).log', 'size': 5830},
            {'name': 'Disc 2/Various Artists - Across The Universe (Deluxe Edition) (Disc 2).m3u',
             'size': 1781},
            {'name': 'Folder.jpg', 'size': 55399},
        ])
        self.assertEqual(torrent.info_image_files, [
            {'name': 'Folder.jpg', 'size': 55399},
        ])
        self.assertEqual(torrent.info_has_artwork, False)
        self.assertEqual(torrent.info_size, 640020399)


class ReplicaSetTests(TestCase):
    fixtures = ['replica_sets.json']

    def setUp(self):
        super(ReplicaSetTests, self).setUp()

    def test_get_master(self):
        what_master = ReplicaSet.get_what_master()
        self.assertEqual(what_master.zone, ReplicaSet.ZONE_WHAT)
        self.assertEqual(what_master.name, 'master')
        bib_master = ReplicaSet.get_bibliotik_master()
        self.assertEqual(bib_master.zone, ReplicaSet.ZONE_BIBLIOTIK)
        self.assertEqual(bib_master.name, 'master')
