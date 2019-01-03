from django.core.management.base import BaseCommand

from books.models import BookUpload
from home.models import WhatTorrent, TransTorrent, WhatFulltext, WhatFileMetadataCache, \
    WhatLoginCache, ReplicaSet
from what_transcode.models import TranscodeRequest


class Command(BaseCommand):
    help = 'Clears the database of what torrents, trans torrents, also removes all torrents from transmission'

    def handle(self, *args, **options):
        print('Deleting BookUpload...')
        BookUpload.objects.all().delete()
        print('Deleting TranscodeRequest...')
        TranscodeRequest.objects.all().delete()
        print('Deleting WhatLoginCache...')
        WhatLoginCache.objects.all().delete()
        print('Deleting WhatFileMetadataCache...')
        WhatFileMetadataCache.objects.all().delete()
        print('Deleting WhatFulltext...')
        WhatFulltext.objects.all().delete()
        print('Deleting TransTorrent...')
        TransTorrent.objects.all().delete()
        print('Deleting WhatTorrent...')
        WhatTorrent.objects.all().delete()
        # Delete all torrents
        for instance in ReplicaSet.objects.get(zone='what.cd').transinstance_set.all():
            print('Fetching torrents from', instance.name)
            torrent_ids = [t.id for t in instance.client.get_torrents(arguments=['id'])]
            print('Removing torrents')
            instance.client.remove_torrent(torrent_ids)
