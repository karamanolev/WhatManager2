import json

from django.core.management.base import BaseCommand
from django.forms.models import model_to_dict

from home.models import ReplicaSet


def date_handler(obj):
    if hasattr(obj, 'isoformat'):
        return obj.isoformat()
    else:
        raise TypeError


class Command(BaseCommand):
    help = 'Export transmission torrents and what torrents'

    def handle(self, *args, **options):
        output = open('what_manager2_torrents.jsonl', 'wb')
        what_replica = ReplicaSet.objects.get(zone='what.cd', name='master')
        counter = 0
        for instance in what_replica.transinstance_set.all():
            print('Process instance', instance.name)
            t_torrents = instance.transtorrent_set.all().select_related('what_torrent', 'location')
            for t_torrent in t_torrents:
                output.write(json.dumps({
                    'trans_torrent': model_to_dict(t_torrent),
                    'what_torrent': model_to_dict(t_torrent.what_torrent),
                    'location': model_to_dict(t_torrent.location),
                }, default=date_handler))
                output.write('\n')
                counter += 1
                if counter % 1000 == 0:
                    print('Done', counter)
        print('Total done:', counter)
