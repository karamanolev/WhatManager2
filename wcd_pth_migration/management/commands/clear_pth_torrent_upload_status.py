from django.core.management.base import BaseCommand

from wcd_pth_migration.models import WhatTorrentMigrationStatus


class Command(BaseCommand):
    help = 'Saves the current complete uploads as WhatTorrentGroupMatching objects'

    def add_arguments(self, parser):
        parser.add_argument('what_torrent_id')

    def handle(self, *args, **options):
        torrent_id = options['what_torrent_id']
        WhatTorrentMigrationStatus.objects.get(what_torrent_id=torrent_id).delete()
