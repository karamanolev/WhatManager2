# -*- coding: utf-8 -*-


from django.test.testcases import TestCase
from mock import patch

from WhatManager2.management.commands import transmission_provision
from WhatManager2.utils import get_artists, get_artists_list


@patch('WhatManager2.management.commands.transmission_provision.confirm')
class ProvisioningTests(TestCase):
    def test_ensure_replica_sets_exist(self, mock_confirm):
        transmission_provision.ensure_replica_sets_exist()
        self.assertEqual(transmission_provision.confirm.call_count, 2)


class GetArtistsTests(TestCase):
    def test_plain_artists(self):
        artists = {"musicInfo": {
            "composers": [],
            "dj": [],
            "artists": [
                {"id": 3632, "name": "Supertramp"}
            ],
            "with": [],
            "conductor": [],
            "remixedBy": [],
            "producer": [],
        }}
        self.assertEqual(get_artists(artists), 'Supertramp')
        self.assertEqual(get_artists_list(artists), [
            {'id': 3632, 'name': 'Supertramp', 'join': ''},
        ])

    def test_composer_performed_by_various(self):
        artists = {"musicInfo": {
            "composers": [{"id": 18505, "name": "Rob Swift"}],
            "dj": [],
            "artists": [
                {"id": 34715, "name": "Al Hirt"},
                {"id": 270168, "name": "Boulaone"},
                {"id": 270167, "name": "Bronislau Kaper"},
                {"id": 6889, "name": "Dizzy Gillespie"},
                {"id": 4570, "name": "Eddie Harris"},
                {"id": 1906, "name": "Herbie Hancock"},
                {"id": 23734, "name": "Large Professor"},
                {"id": 19913, "name": "Les McCann"},
                {"id": 1181, "name": "Lou Donaldson"},
                {"id": 117375, "name": "Richard Evans"},
            ],
            "with": [
                {"id": 21519, "name": "Bob James"},
                {"id": 194729, "name": "Dave McMurray"},
                {"id": 76312, "name": "Dujeous"},
                {"id": 270169, "name": "Isaman"},
                {"id": 270170, "name": "Legrotony"},
            ],
            "conductor": [],
            "remixedBy": [],
            "producer": [],
        }}
        self.assertEqual(get_artists(artists), 'Rob Swift performed by Various Artists')
        self.assertEqual(get_artists_list(artists), [
            {'id': 18505, 'name': 'Rob Swift', 'join': ' performed by '},
            {'id': -1, 'name': 'Various Artists', 'join': ''},
        ])

    def test_composer_performed_by_two(self):
        artists = {"musicInfo": {
            "composers": [
                {"id": 64138, "name": "Mikis Theodorakis (Μίκης Θεοδωράκης)"}
            ],
            "dj": [],
            "artists": [
                {"id": 5606, "name": "John Williams"},
                {"id": 328352, "name": "Maria Farantouri (Μαρία Φαραντούρη)"}
            ],
            "with": [],
            "conductor": [],
            "remixedBy": [],
            "producer": []
        }}
        self.assertEqual(get_artists(artists),
                         'Mikis Theodorakis (Μίκης Θεοδωράκης) performed by John Williams & '
                         'Maria Farantouri (Μαρία Φαραντούρη)')
        self.assertEqual(get_artists_list(artists), [
            {'id': 64138, 'name': 'Mikis Theodorakis (Μίκης Θεοδωράκης)', 'join': ' performed by '},
            {'id': 5606, 'name': 'John Williams', 'join': ' & '},
            {'id': 328352, 'name': 'Maria Farantouri (Μαρία Φαραντούρη)', 'join': ''},
        ])

    def test_composer_performed_by_various_under_conductor(self):
        artists = {"musicInfo": {
            "composers": [
                {"id": 33445, "name": "Joaquín Rodrigo"}
            ],
            "dj": [],
            "artists": [
                {"id": 781081, "name": "Alexandre Logoya"},
                {"id": 517621, "name": "Catherine Michel"},
                {"id": 150064, "name": "Orchestre National de l'Opéra de Monte-Carlo"}
            ],
            "with": [],
            "conductor": [
                {"id": 407370, "name": "Antonio de Almeida"}
            ],
            "remixedBy": [],
            "producer": []
        }}
        self.assertEqual(get_artists(artists), 'Joaquín Rodrigo performed by Various Artists under '
                                               'Antonio de Almeida')
        self.assertEqual(get_artists_list(artists), [
            {'id': 33445, 'name': 'Joaquín Rodrigo', 'join': ' performed by '},
            {'id': -1, 'name': 'Various Artists', 'join': ' under '},
            {'id': 407370, 'name': 'Antonio de Almeida', 'join': ''},
        ])

    def test_two_composers_many_artists(self):
        artists = {"musicInfo": {
            "composers": [
                {"id": 1031282, "name": "Anónimo"},
                {"id": 1089741, "name": "Georg-Friedrich Haendel"},
                {"id": 1089740, "name": "Georg-Philipp Telemann"},
                {"id": 6522, "name": "Johann Sebastian Bach"},
                {"id": 1089742, "name": "Johann-Jakob van Eyck"},
                {"id": 35746, "name": "John Dowland"}
            ],
            "dj": [],
            "artists": [
                {"id": 1089739, "name": "Andras Kecskés"},
                {"id": 464752, "name": "René Clemencic"}
            ],
            "with": [],
            "conductor": [],
            "remixedBy": [],
            "producer": []
        }}
        self.assertEqual(get_artists(artists), 'Andras Kecskés & René Clemencic')
        self.assertEqual(get_artists_list(artists), [
            {'id': 1089739, 'name': 'Andras Kecskés', 'join': ' & '},
            {'id': 464752, 'name': 'René Clemencic', 'join': ''},
        ])
