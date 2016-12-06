from django.core.management.base import BaseCommand

from home.models import WhatTorrent, TransTorrent, WhatFulltext, WhatFileMetadataCache, \
    WhatLoginCache, ReplicaSet


class Command(BaseCommand):
    help = 'Clears the database of what torrents, trans torrents, also removes all torrents from transmission'

    def handle(self, *args, **options):
        WhatLoginCache.objects.all().delete()
        WhatFileMetadataCache.objects.all().delete()
        WhatFulltext.objects.all().delete()
        TransTorrent.objects.all().delete()
        WhatTorrent.objects.all().delete()
        # Delete all torrents
        for instance in ReplicaSet.objects.get(zone='what.cd').transinstance_set.all():
            print 'Fetching torrents from', instance.name
            torrent_ids = [t.id for t in instance.client.get_torrents(arguments=['id'])]
            print 'Removing torrents'
            instance.client.remove_torrent(torrent_ids)
