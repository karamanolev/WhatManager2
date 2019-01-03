import ujson

from django.core.management.base import BaseCommand

from home.models import get_what_client, BadIdException
from wcd_pth_migration.models import WhatTorrentMigrationStatus, TorrentGroupMapping


class Command(BaseCommand):
    help = 'Saves the current complete uploads as WhatTorrentGroupMatching objects'

    def handle(self, *args, **options):
        what = get_what_client(lambda: None, True)
        with open('what_manager2_torrents.jsonl', 'rb') as torrents_input:
            for line in torrents_input:
                data = ujson.loads(line)
                info = ujson.loads(data['what_torrent']['info'])
                what_torrent_id = info['torrent']['id']
                what_group_id = info['group']['id']
                try:
                    TorrentGroupMapping.objects.get(what_group_id=what_group_id)
                    continue
                except TorrentGroupMapping.DoesNotExist:
                    pass
                try:
                    migration_status = WhatTorrentMigrationStatus.objects.get(
                        what_torrent_id=what_torrent_id)
                except WhatTorrentMigrationStatus.DoesNotExist:
                    continue
                if migration_status.status != WhatTorrentMigrationStatus.STATUS_COMPLETE:
                    continue
                pth_torrent_id = migration_status.pth_torrent_id
                if not pth_torrent_id:
                    continue
                try:
                    pth_torrent = what.request('torrent', id=pth_torrent_id)['response']
                except BadIdException:
                    continue
                pth_group_id = pth_torrent['group']['id']
                print('Saving {} mapping to {}'.format(what_group_id, pth_group_id))
                TorrentGroupMapping.objects.create(
                    what_group_id=what_group_id,
                    pth_group_id=pth_group_id,
                )
