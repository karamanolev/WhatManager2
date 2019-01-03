from django.db import models, transaction

from django.utils import timezone
from django.utils.functional import cached_property

import ujson
from WhatManager2.utils import html_unescape, get_artists


class WhatArtistAlias(models.Model):
    artist = models.ForeignKey('WhatArtist', on_delete=models.CASCADE)
    name = models.CharField(max_length=200, unique=True)

    def save(self, *args, **kwargs):
        super(WhatArtistAlias, self).save(*args, **kwargs)
        WhatMetaFulltext.create_or_update_artist_alias(self)

    @classmethod
    def get_or_create(cls, artist, name):
        try:
            return artist.whatartistalias_set.get(name=name)
        except WhatArtistAlias.DoesNotExist:
            alias = WhatArtistAlias(
                artist=artist,
                name=name,
            )
            alias.save()
            return alias


# Lengths taken from gazelle.sql from GitHub
class WhatArtist(models.Model):
    retrieved = models.DateTimeField(db_index=True)
    name = models.CharField(max_length=200, db_index=True)
    image = models.CharField(max_length=255, null=True)
    wiki_body = models.TextField(null=True)
    vanity_house = models.BooleanField(default=False)
    info_json = models.TextField(null=True)

    @cached_property
    def info(self):
        if self.info_json is None:
            return None
        return ujson.loads(self.info_json)

    @cached_property
    def fulltext_info(self):
        return self.name

    @cached_property
    def fulltext_more_info(self):
        return ''

    @property
    def is_shell(self):
        return self.info_json is None

    def save(self, *args, **kwargs):
        super(WhatArtist, self).save(*args, **kwargs)
        WhatMetaFulltext.create_or_update_artist(self)

    @classmethod
    def get_or_create_shell(cls, artist_id, name, retrieved):
        try:
            artist = WhatArtist.objects.get(id=artist_id)
            alias = None
            if artist.name != name:
                alias = WhatArtistAlias.get_or_create(artist, name)
            return artist, alias
        except WhatArtist.DoesNotExist:
            new_artist = WhatArtist(
                id=artist_id,
                name=name,
                retrieved=retrieved,
            )
            new_artist.save()
            return new_artist, None

    @classmethod
    def update_from_what(cls, what_client, artist_id):
        try:
            artist = WhatArtist.objects.get(id=artist_id)
        except WhatArtist.DoesNotExist:
            artist = WhatArtist(
                id=artist_id
            )
        retrieved = timezone.now()
        response = what_client.request('artist', id=artist_id)['response']

        artist.retrieved = retrieved
        old_name = artist.name
        artist.name = html_unescape(response['name'])
        artist.image = html_unescape(response['image'])
        artist.wiki_body = response['body']
        artist.vanity_house = response['vanityHouse']
        artist.info_json = ujson.dumps(response)

        if old_name and artist.name != old_name:
            try:
                old_alias = artist.whatartistalias_set.get(name=artist.name)
                old_alias.delete()
            except WhatArtistAlias.DoesNotExist:
                pass
            with transaction.atomic():
                artist.save()
                WhatArtistAlias.get_or_create(artist, old_name)
        else:
            artist.save()

        return artist


class WhatTorrentGroup(models.Model):
    retrieved = models.DateTimeField()
    artists = models.ManyToManyField(WhatArtist, through='WhatTorrentArtist')
    wiki_body = models.TextField()
    wiki_image = models.CharField(max_length=255)
    joined_artists = models.TextField()
    name = models.CharField(max_length=300)  # Indexed with a RunSQL migration
    year = models.IntegerField()
    record_label = models.CharField(max_length=80)
    catalogue_number = models.CharField(max_length=80)
    release_type = models.IntegerField()
    category_id = models.IntegerField()
    category_name = models.CharField(max_length=32)
    time = models.DateTimeField()
    vanity_house = models.BooleanField(default=False)
    info_json = models.TextField()
    # Will contain the JSON for the "torrent" response field if this was fetched through
    # action=torrentgroup. If it was created from an action=torrent, then it will be NULL
    torrents_json = models.TextField(null=True)

    @cached_property
    def info(self):
        return ujson.loads(self.info_json)

    @cached_property
    def torrents(self):
        return ujson.loads(self.torrents_json)

    @cached_property
    def fulltext_info(self):
        return self.name

    @cached_property
    def fulltext_more_info(self):
        return self.joined_artists + ' ' + str(self.year) + ' ' + self.catalogue_number

    def add_artists(self, importance, artists):
        for artist in artists:
            what_artist, artist_alias = WhatArtist.get_or_create_shell(
                artist['id'], html_unescape(artist['name']), self.retrieved)
            WhatTorrentArtist(
                artist=what_artist,
                artist_alias=artist_alias,
                torrent_group=self,
                importance=importance,
            ).save()

    def save(self, *args, **kwargs):
        super(WhatTorrentGroup, self).save(*args, **kwargs)
        WhatMetaFulltext.create_or_update_torrent_group(self)

    @classmethod
    def update_if_newer(cls, group_id, retrieved, data_dict, torrents_dict=None):
        try:
            group = WhatTorrentGroup.objects.get(id=group_id)
            if retrieved < group.retrieved:
                return group
        except WhatTorrentGroup.DoesNotExist:
            group = WhatTorrentGroup(
                id=group_id
            )
        group.retrieved = retrieved
        group.wiki_body = data_dict['wikiBody']
        group.wiki_image = html_unescape(data_dict['wikiImage'])
        group.joined_artists = get_artists(data_dict)
        group.name = html_unescape(data_dict['name'])
        group.year = data_dict['year']
        group.record_label = html_unescape(data_dict['recordLabel'])
        group.catalogue_number = html_unescape(data_dict['catalogueNumber'])
        group.release_type = data_dict['releaseType']
        group.category_id = data_dict['categoryId']
        group.category_name = data_dict['categoryName']
        group.time = data_dict['time']
        group.vanity_house = data_dict['vanityHouse']
        group.info_json = ujson.dumps(data_dict)
        if torrents_dict is not None:
            group.torrents_json = ujson.dumps(torrents_dict)
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
    artist = models.ForeignKey(WhatArtist, on_delete=models.CASCADE)
    artist_alias = models.ForeignKey(WhatArtistAlias, null=True, on_delete=models.CASCADE)
    torrent_group = models.ForeignKey(WhatTorrentGroup, on_delete=models.CASCADE)
    importance = models.IntegerField()


class WhatMetaFulltext(models.Model):
    info = models.TextField()
    more_info = models.TextField()
    artist = models.OneToOneField(WhatArtist, null=True, on_delete=models.CASCADE)
    artist_alias = models.OneToOneField(WhatArtistAlias, null=True, on_delete=models.CASCADE)
    torrent_group = models.OneToOneField(WhatTorrentGroup, null=True, on_delete=models.CASCADE)

    @classmethod
    def create_or_update_artist(cls, artist):
        info = artist.fulltext_info
        more_info = artist.fulltext_more_info
        try:
            fulltext = WhatMetaFulltext.objects.get(artist=artist)
            if fulltext.info == info and fulltext.more_info == more_info:
                return fulltext
        except WhatMetaFulltext.DoesNotExist:
            fulltext = WhatMetaFulltext(artist=artist)
        fulltext.info = info
        fulltext.more_info = more_info
        fulltext.save()
        return fulltext

    @classmethod
    def create_or_update_artist_alias(cls, artist_alias):
        info = artist_alias.name
        try:
            fulltext = WhatMetaFulltext.objects.get(artist_alias=artist_alias)
            if fulltext.info == info and fulltext.more_info == '':
                return fulltext
        except WhatMetaFulltext.DoesNotExist:
            fulltext = WhatMetaFulltext(artist_alias=artist_alias)
        fulltext.info = info
        fulltext.more_info = ''
        fulltext.save()
        return fulltext

    @classmethod
    def create_or_update_torrent_group(cls, torrent_group):
        info = torrent_group.fulltext_info
        more_info = torrent_group.fulltext_more_info
        try:
            fulltext = WhatMetaFulltext.objects.get(torrent_group=torrent_group)
            if fulltext.info == info and fulltext.more_info == more_info:
                return fulltext
        except WhatMetaFulltext.DoesNotExist:
            fulltext = WhatMetaFulltext(torrent_group=torrent_group)
        fulltext.info = info
        fulltext.more_info = more_info
        fulltext.save()
        return fulltext
