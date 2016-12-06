from django.db import models


class DownloadLocationEquivalent(models.Model):
    old_location = models.CharField(max_length=512)
    new_location = models.CharField(max_length=512)


class WhatTorrentMigrationStatus(models.Model):
    STATUS_PROCESSING = 0
    STATUS_DUPLICATE = 1
    STATUS_SKIPPED = 2
    STATUS_UPLOADED = 3
    STATUS_COMPLETE = 4
    STATUS_SKIPPED_PERMANENTLY = 5

    what_torrent_id = models.BigIntegerField(unique=True)
    status = models.IntegerField()
