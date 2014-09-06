from django.db import models, transaction

# Lengths taken from gazelle.sql from GitHub
from django.db.backends.mysql.base import parse_datetime_with_timezone_support


class WhatArtist(models.Model):
    retrieved = models.DateTimeField()
    name = models.CharField(max_length=200)
    image = models.CharField(max_length=255, null=True)
    wiki = models.TextField(null=True)
    vanity_house = models.BooleanField(null=True)

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


class WhatTorrentArtist(models.Model):
    artist = models.ForeignKey(WhatArtist)
    torrent_group = models.ForeignKey(WhatTorrentGroup)
    importance = models.IntegerField()


class WhatTorrentGroup(models.Model):
    retrieved = models.DateTimeField()
    artists = models.ManyToManyField(WhatArtist, through=WhatTorrentArtist)
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
    vanity_house = models.BooleanField()

    @classmethod
    def update_if_newer(cls, group_id, retrieved, data_dict):
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
        with transaction.atomic():
            group.save()
            group.artists.clear()
            def add_artists(importance, artists):
                for artist in artists:
                    what_artist = WhatArtist.get_or_create_shell(
                        artist['id'], artist['name'], retrieved)
                    WhatTorrentArtist(
                        artist=what_artist,
                        torrent_group=group,
                        importance=importance
                    ).save()
            add_artists(1, data_dict['musicInfo']['artists'])
            add_artists(2, data_dict['musicInfo']['with'])
            add_artists(3, data_dict['musicInfo']['remixedBy'])
            add_artists(4, data_dict['musicInfo']['composers'])
            add_artists(5, data_dict['musicInfo']['conductor'])
            add_artists(6, data_dict['musicInfo']['dj'])
            add_artists(7, data_dict['musicInfo']['producer'])
