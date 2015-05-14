from time import sleep

from django.core.management.base import BaseCommand

from bibliotik import manage_bibliotik
from bibliotik.models import BibliotikTorrent, BibliotikTorrentPageCache
from bibliotik.utils import BibliotikClient


class Command(BaseCommand):
    help = 'Clears and rebuilds the Biblitoik fulltext table.'

    def handle(self, *args, **options):
        client = BibliotikClient(args[0])
        cache_items = list(BibliotikTorrentPageCache.objects.filter(status_code=200).order_by('id').all())
        for item in cache_items:
            t = BibliotikTorrent(id=item.id, html_page=item.body)
            try:
                print 'Parsing', item.id
                t.parse_html_page()
                if t.category != 'Ebooks':
                    continue
                if t.torrent_size > 50 * 1000 ** 2:
                    continue
                if t.bibliotiktranstorrent_set.count() > 0:
                    continue
                print 'Will download:'
                print ' {' + str(t.id) + '}', t.title
                print t.torrent_size
                manage_bibliotik.add_bibliotik_torrent(t.id, bibliotik_client=client)
                print 'Added'
                sleep(5)
            except AssertionError:
                pass