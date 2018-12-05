from django.core.management.base import BaseCommand

from bibliotik.models import BibliotikFulltext, BibliotikTorrent


class Command(BaseCommand):
    help = 'Clears and rebuilds the Biblitoik fulltext table.'

    def handle(self, *args, **options):
        print('Deleting all fulltext entries...')
        BibliotikFulltext.objects.all().delete()
        print('Fetching Bibliotik torrents...')
        torrents = list(BibliotikTorrent.objects.defer('html_page', 'torrent_file').all())
        print('Got {0} torrents. Creating fulltext entries...'.format(len(torrents)))
        updated = 0
        for t in torrents:
            ft = BibliotikFulltext(
                id=t.id
            )
            ft.update(t)
            updated += 1
            if updated % 200 == 0:
                print('Updated {0}/{1} torrents...'.format(updated, len(torrents)))
        print('Successfully updated {0} torrents.'.format(len(torrents)))
