import json
import os

from django.core.management.base import BaseCommand

from home.models import ReplicaSet, DownloadLocation
from wcd_pth_migration.utils import generate_spectrals_for_dir


class Command(BaseCommand):
    help = 'Clears the database of what torrents, trans torrents, also removes all torrents from transmission'

    def handle(self, *args, **options):
        checked = []
        try:
            with open('checked.json', 'r') as f:
                checked = json.loads(f.read())
        except IOError:
            pass
        for dl in DownloadLocation.objects.filter(zone=ReplicaSet.ZONE_WHAT):
            for torrent in os.listdir(dl.path):
                if torrent in checked:
                    print('Already checked', torrent, 'skipping...')
                    continue
                torrent_path = os.path.join(dl.path, torrent)
                print('Generating spectrals for', torrent_path)
                if not generate_spectrals_for_dir(torrent_path):
                    print('There are no FLACs, moving on...')
                else:
                    input('Please check the spectrals...')
                checked.append(torrent)
                with open('checked.json', 'w') as f:
                    f.write(json.dumps(checked))
