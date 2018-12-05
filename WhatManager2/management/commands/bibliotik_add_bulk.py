from optparse import make_option
from time import sleep

from django.core.management.base import BaseCommand

from bibliotik import manage_bibliotik
from bibliotik.models import BibliotikTorrent, BibliotikTorrentPageCache
from bibliotik.utils import BibliotikClient


class Command(BaseCommand):
    option_list = BaseCommand.option_list + (
        make_option('--start-index',
                    action='store',
                    dest='start_index',
                    default=1,
                    help='The torrent index to start with, if all have been completed up to an index.'),
    )
    help = 'Clears and rebuilds the Biblitoik fulltext table.'

    def handle(self, *args, **options):
        client = BibliotikClient(args[0])
        start_index = options['start_index']
        cache_items = list(BibliotikTorrentPageCache.objects.filter(
            status_code=200, id__gte=start_index).order_by('id').all())
        for item in cache_items:
            t = BibliotikTorrent(id=item.id, html_page=item.body)
            try:
                print('Parsing', item.id)
                t.parse_html_page()
                if t.category != 'Ebooks':
                    continue
                # if t.torrent_size > 500 * 1000 ** 2:
                #     continue
                if t.bibliotiktranstorrent_set.count() > 0:
                    continue
                print('Will download:')
                print(' {' + str(t.id) + '}', t.title)
                print(t.torrent_size)
                manage_bibliotik.add_bibliotik_torrent(t.id, bibliotik_client=client)
                print('Added')
                sleep(1.5)
            except AssertionError:
                pass
