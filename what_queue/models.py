from django.db import models

from home.info_holder import get_release_type_id
from home.models import WhatTorrent


RELEASE_PRIORITIES = [
    (get_release_type_id('Album'), 1000),
    (get_release_type_id('EP'), 990),
    (get_release_type_id('Soundtrack'), 986),
    # (get_release_type_id('Single'), 985),
    (get_release_type_id('Live album'), 980),
]


def get_priority(release_type):
    for priority in RELEASE_PRIORITIES:
        if priority[0] == int(release_type):
            return priority[1]
    return None


def filter_group(artist_name, group):
    if get_priority(group['releaseType']) is None:
        return False
    if not group['artists']:
        return False
    if not any(a['name'] == artist_name for a in group['artists']):
        return False
    return True


def filter_torrent(group, torrent):
    if torrent['format'].lower() != 'flac':
        return False
    if torrent['media'].lower() not in ['cd', 'web']:
        return False
    return get_priority(group['releaseType'])


def is_existing(what_id):
    try:
        QueueItem.objects.get(what_id=what_id)
        return True
    except QueueItem.DoesNotExist:
        return WhatTorrent.is_downloaded(None, what_id=what_id)


class QueueItem(models.Model):
    datetime_added = models.DateTimeField(auto_now_add=True)
    what_id = models.IntegerField()
    priority = models.IntegerField()

    artist = models.TextField()
    title = models.TextField()
    release_type = models.IntegerField()
    format = models.TextField()
    encoding = models.TextField()
    torrent_size = models.BigIntegerField()

    @classmethod
    def get_front(cls):
        items = QueueItem.objects.order_by('-priority', 'datetime_added')[:1]
        if len(items):
            return items[0]
        return None
