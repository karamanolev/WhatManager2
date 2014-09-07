import json

from django.db import models, transaction


# Lengths taken from gazelle.sql from GitHub
from django.db.backends.mysql.base import parse_datetime_with_timezone_support
from django.utils import timezone


class WhatArtist(models.Model):
    retrieved = models.DateTimeField()
    name = models.CharField(max_length=200)
    image = models.CharField(max_length=255, null=True)
    wiki_body = models.TextField(null=True)
    vanity_house = models.BooleanField(default=False)

    @classmethod
    def get_or_create_shell(cls, artist_id, name, retrieved):
        try:
            return WhatArtist.objects.get(id=artist_id)
        except WhatArtist.DoesNotExist:
            new_artist = WhatArtist(
                id=artist_id,
                name=name,
                retrieved=retrieved,
            )
            new_artist.save()
            return new_artist


class WhatTorrentGroup(models.Model):
    retrieved = models.DateTimeField()
    artists = models.ManyToManyField(WhatArtist, through='WhatTorrentArtist')
    wiki_body = models.TextField()
    wiki_image = models.CharField(max_length=255)
    name = models.CharField(max_length=300)
    year = models.IntegerField()
    record_label = models.CharField(max_length=80)
    catalogue_number = models.CharField(max_length=80)
    release_type = models.IntegerField()
    category_id = models.IntegerField()
    category_name = models.CharField(max_length=32)
    time = models.DateTimeField()
    vanity_house = models.BooleanField(default=False)
    # Will contain the JSON for the "torrent" response field if this was fetched through
    # action=torrentgroup. If it was created from an action=torrent, then it will be NULL
    torrents_json = models.TextField(null=True)

    def add_artists(self, importance, artists):
        for artist in artists:
            what_artist = WhatArtist.get_or_create_shell(
                artist['id'], artist['name'], self.retrieved)
            WhatTorrentArtist(
                artist=what_artist,
                torrent_group=self,
                importance=importance
            ).save()

    @classmethod
    def update_if_newer(cls, group_id, retrieved, data_dict, torrents_dict=None):
        try:
            group = WhatTorrentGroup.objects.get(id=group_id)
            if retrieved < group.retrieved:
                return
        except WhatTorrentGroup.DoesNotExist:
            group = WhatTorrentGroup(
                id=group_id
            )
        group.retrieved = retrieved
        group.wiki_body = data_dict['wikiBody']
        group.wiki_image = data_dict['wikiImage']
        group.name = data_dict['name']
        group.year = data_dict['year']
        group.record_label = data_dict['recordLabel']
        group.catalogue_number = data_dict['catalogueNumber']
        group.release_type = data_dict['releaseType']
        group.category_id = data_dict['categoryId']
        group.category_name = data_dict['categoryName']
        group.time = parse_datetime_with_timezone_support(data_dict['time'])
        group.vanity_house = data_dict['vanityHouse']
        if torrents_dict is not None:
            group.torrents_json = json.dumps(torrents_dict)
        else:
            group.torrents_json = None
        with transaction.atomic():
            group.save()
            group.artists.clear()
            group.add_artists(1, data_dict['musicInfo']['artists'])
            group.add_artists(2, data_dict['musicInfo']['with'])
            group.add_artists(3, data_dict['musicInfo']['remixedBy'])
            group.add_artists(4, data_dict['musicInfo']['composers'])
            group.add_artists(5, data_dict['musicInfo']['conductor'])
            group.add_artists(6, data_dict['musicInfo']['dj'])
            group.add_artists(7, data_dict['musicInfo']['producer'])
        return group

    @classmethod
    def update_from_what(cls, what_client, group_id):
        retrieved = timezone.now()
        group = what_client.request('torrentgroup', id=group_id)['response']
        return cls.update_if_newer(group_id, retrieved, group['group'], group['torrents'])


class WhatTorrentArtist(models.Model):
    artist = models.ForeignKey(WhatArtist)
    torrent_group = models.ForeignKey(WhatTorrentGroup)
    importance = models.IntegerField()