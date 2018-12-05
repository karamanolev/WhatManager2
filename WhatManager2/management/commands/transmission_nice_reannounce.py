from optparse import make_option
import time

from django.core.management.base import BaseCommand

from home.models import ReplicaSet


BATCH_SIZE = 50


def is_torrent_errored(torrent):
    if torrent.error:
        return True
    for tracker in torrent.trackerStats:
        if not tracker['lastAnnounceSucceeded']:
            return True
    return False


class Command(BaseCommand):
    option_list = BaseCommand.option_list + (
        make_option('--zone',
                    action='store',
                    dest='zone',
                    help='Zone to reannounce'),
        make_option('--fast',
                    action='store_true',
                    dest='fast',
                    default=False,
                    help='Reannounce faster'),
    )

    def __init__(self):
        super(Command, self).__init__()
        self.sleep_time = None

    def reannounce_zone(self, replica_set):
        for instance in replica_set.transinstance_set.all():
            print('Reannouncing {0}'.format(instance))
            client = instance.client
            torrents = client.get_torrents(arguments=[
                'id', 'name', 'error', 'errorString', 'status', 'trackerStats'])
            error_torrents = [t for t in torrents if is_torrent_errored(t)]
            batch_start = 0
            while batch_start < len(error_torrents):
                batch = error_torrents[batch_start:batch_start + BATCH_SIZE]
                print('Processing batch from {0} to {1} / {2}'.format(
                    batch_start, batch_start + len(batch), len(error_torrents)))
                batch_start += len(batch)
                client.reannounce_torrent([t.id for t in batch])
                time.sleep(self.sleep_time)

    def handle(self, *args, **options):
        self.sleep_time = 0.5 if options['fast'] else 2.0
        if options['zone']:
            master = ReplicaSet.objects.get(zone=options['zone'], name='master')
            self.reannounce_zone(master)
        else:
            for master in ReplicaSet.objects.filter(name='master'):
                print('Reannouncing zone {0}'.format(master.zone))
                self.reannounce_zone(master)
