import json

from django.utils import timezone

from home.models import RequestException, TransTorrent, ReplicaSet, WhatTorrent


def refresh_whattorrent(what_client, what_torrent=None):
    if what_torrent is None:
        what_torrent = WhatTorrent.objects.defer('torrent_file').order_by('retrieved')[0]

    try:
        response = what_client.request('torrent', id=what_torrent.id)['response']
    except RequestException as ex:
        if ex.response and type(ex.response) is dict and ex.response.get(
                'error') == 'bad id parameter':
            try:
                TransTorrent.objects.get(
                    instance__in=ReplicaSet.get_what_master().transinstance_set.all(),
                    what_torrent=what_torrent)
                return {
                    'success': False,
                    'id': what_torrent.id,
                    'status': 'missing',
                }
            except TransTorrent.DoesNotExist:
                what_torrent.delete()
                return {
                    'success': True,
                    'id': what_torrent.id,
                    'status': 'deleted',
                }
        else:
            return {
                'success': False,
                'status': 'unknown request exception',
            }

    old_retrieved = what_torrent.retrieved
    what_torrent.info = json.dumps(response)
    what_torrent.retrieved = timezone.now()
    what_torrent.save()
    return {
        'success': True,
        'id': what_torrent.id,
        'status': 'refreshed',
        'retrieved': str(old_retrieved),
    }
