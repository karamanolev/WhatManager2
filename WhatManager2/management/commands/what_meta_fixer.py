from django.core.management.base import BaseCommand
from django.db import transaction

from home.models import WhatTorrent


class Command(BaseCommand):
    help = 'Fixes missing entries in what_meta by iterating `WhatTorrent`s.'

    def handle(self, *args, **options):
        print('Running what_meta fixer...')
        print('Fixing WhatTorrent -> WhatTorrentGroup mapping')
        what_torrent_ids = WhatTorrent.objects.filter(torrent_group=None).values_list(
            'id', flat=True)
        start = 0
        page_size = 128
        while start < len(what_torrent_ids):
            print('Updating objects {0}-{1}/{2}'.format(start, start + page_size,
                                                        len(what_torrent_ids)))
            bulk = WhatTorrent.objects.defer('torrent_file').in_bulk(
                what_torrent_ids[start:start + page_size])
            start += page_size
            with transaction.atomic():
                for torrent in list(bulk.values()):
                    # Skip non-music torrents for now
                    if torrent.info_category_id != 1:
                        continue
                    try:
                        torrent.save()
                    except Exception as ex:
                        print('Error updating what_id={0}: {1}'.format(torrent.id, ex))
        print('Completed.')
