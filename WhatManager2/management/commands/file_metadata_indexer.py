from django.core.management.base import BaseCommand

from home.models import ReplicaSet, WhatTorrent, \
    TransTorrent, WhatFileMetadataCache


class Command(BaseCommand):
    help = 'Cache all .flac and .mp3 metadata in download locations.'

    def handle(self, *args, **options):
        masters = ReplicaSet.get_what_master().transinstance_set.all()
        what_torrent_ids = WhatTorrent.objects.all().values_list('id', flat=True)
        start = 0
        page_size = 128
        while start < len(what_torrent_ids):
            print('Updating objects {0}-{1}/{2}'.format(start, start + page_size,
                                                        len(what_torrent_ids)))
            bulk = WhatTorrent.objects.defer('torrent_file').in_bulk(
                what_torrent_ids[start:start + page_size])
            start += page_size
            trans_torrents = {
                t.what_torrent_id: t for t in
                TransTorrent.objects.filter(instance__in=masters, what_torrent__in=list(bulk.values()))
            }
            for what_torrent in bulk.values():
                trans_torrent = trans_torrents.get(what_torrent.id)
                if trans_torrent is not None and trans_torrent.torrent_done == 1:
                    try:
                        WhatFileMetadataCache.get_metadata_batch(what_torrent, trans_torrent, True)
                    except Exception as ex:
                        print('Failed updating torrent {0}: {1}'.format(what_torrent.id, ex))
