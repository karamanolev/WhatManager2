from django.core.management.base import BaseCommand
from django.db import transaction


class Command(BaseCommand):
    help = 'Fixes missing entries in what_meta by iterating `WhatTorrent`s.'

    def __init__(self, what_torrent_model=None):
        super(Command, self).__init__()
        if what_torrent_model is None:
            from home.models import WhatTorrent

            what_torrent_model = WhatTorrent
        self.WhatTorrent = what_torrent_model

    def handle(self, *args, **options):
        print 'Running what_meta fixer...'
        what_torrent_ids = self.WhatTorrent.objects.filter(torrent_group=None).values_list(
            'id', flat=True)
        start = 0
        page_size = 128
        while start < len(what_torrent_ids):
            print 'Updating objects {0}-{1}/{2}'.format(start, start + page_size,
                                                        len(what_torrent_ids))
            bulk = self.WhatTorrent.objects.defer('torrent_file').in_bulk(
                what_torrent_ids[start:start + page_size]
            )
            start += page_size
            with transaction.atomic():
                for torrent in bulk.values():
                    # Skip non-music torrents for now
                    if torrent.info_category_id != 1:
                        continue
                    try:
                        torrent.save()
                    except Exception as ex:
                        print 'Error updating what_id={0}: {1}'.format(torrent.id, ex)
        print 'Completed.'
