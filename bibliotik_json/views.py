# Create your views here.
import time
import traceback
from json import dumps as json_dumps

from django.contrib.auth.decorators import login_required, user_passes_test
from django.db.models.aggregates import Max
from django.http.response import HttpResponse

from WhatManager2.utils import json_return_method
from bibliotik import manage_bibliotik, trans_sync
from bibliotik.models import BibliotikTransTorrent, BibliotikTorrent, BibliotikTorrentPageCache
from bibliotik.settings import BIBLIOTIK_GET_TORRENT_URL
from bibliotik.utils import BibliotikClient
from home.models import ReplicaSet, LogEntry, TorrentAlreadyAddedException


@login_required
@user_passes_test(lambda u: u.is_superuser is True)
@json_return_method
def sync(request):
    start_time = time.time()

    try:
        master = ReplicaSet.get_bibliotik_master()
        trans_sync.sync_all_instances_db(master)
    except Exception as ex:
        tb = traceback.format_exc()
        LogEntry.add(request.user, 'error', 'Error syncing bibliotik master DB: {0}({1})'
                     .format(type(ex).__name__, ex), tb)
        return {
            'success': False,
            'error': str(ex),
            'traceback': tb
        }

    time_taken = time.time() - start_time
    LogEntry.add(request.user, 'info',
                 'Completed bibliotik sync in {0:.3f}s.'
                 .format(time_taken))
    return {
        'success': True
    }


@login_required
@user_passes_test(lambda u: u.is_superuser is True)
@json_return_method
def add_torrent(request, torrent_id):
    if 'bibliotik_id' not in request.GET:
        return {
            'success': False,
            'error': 'Missing bibliotik_id in GET.',
        }
    bibliotik_client = None
    try:
        bibliotik_id = request.GET['bibliotik_id']
        bibliotik_client = BibliotikClient(bibliotik_id)
        b_torrent = manage_bibliotik.add_bibliotik_torrent(torrent_id,
                                                           bibliotik_client=bibliotik_client)
        bibliotik_torrent = b_torrent.bibliotik_torrent
        LogEntry.add(request.user, 'action', 'Added {0} to {1}'
                     .format(b_torrent, b_torrent.instance))
        return {
            'success': True,
            'title': bibliotik_torrent.title,
            'author': bibliotik_torrent.author,
        }
    except TorrentAlreadyAddedException:
        bibliotik_torrent = None
        try:
            bibliotik_torrent = BibliotikTorrent.objects.get(id=torrent_id)
        except BibliotikTorrent.DoesNotExist:
            pass
        LogEntry.add(request.user, 'info',
                     'Tried adding bibliotik torrent_id={0}, already added.'.format(torrent_id))
        return {
            'success': False,
            'error_code': 'already_added',
            'error': 'Already added.',
            'title': (bibliotik_torrent.title if bibliotik_torrent
                      else '<<< Unable to find torrent >>>'),
            'author': (bibliotik_torrent.author if bibliotik_torrent
                       else '<<< Unable to find torrent >>>'),
        }
    except Exception as ex:
        tb = traceback.format_exc()
        LogEntry.add(request.user, 'error',
                     'Tried adding bibliotik torrent_id={0}. Error: {1}'
                     .format(torrent_id, str(ex)), tb)
        return {
            'success': False,
            'error': str(ex),
            'traceback': tb,
        }


@login_required
@json_return_method
def search(request):
    bibliotik_id = request.GET['bibliotik_id']
    query = request.GET['query']
    bibliotik_client = BibliotikClient(bibliotik_id)
    return bibliotik_client.search(query)


@login_required
@json_return_method
def torrents_info(request):
    include_info_hash = 'info_hash' in request.GET

    def get_response(r_id, r_torrent):
        response = {'id': r_id}
        if r_torrent is None:
            response['status'] = 'missing'
        else:
            if include_info_hash:
                response['info_hash'] = r_torrent.info_hash
            if r_torrent.torrent_done == 1:
                response['status'] = 'downloaded'
            else:
                response['status'] = 'downloading'
                response['progress'] = r_torrent.torrent_done
        return response

    ids = [int(i) for i in request.GET['ids'].split(',')]
    torrents = BibliotikTransTorrent.objects.filter(bibliotik_torrent_id__in=ids)
    torrents = {t.bibliotik_torrent_id: t for t in torrents}
    for torrent in torrents.values():
        if torrent.torrent_done < 1:
            torrent.sync_t_torrent()

    return [get_response(t_id, torrents.get(t_id)) for t_id in ids]


@login_required
@user_passes_test(lambda u: u.is_superuser is True)
def get_torrent_file(request, torrent_id):
    torrent = BibliotikTorrent.objects.get(id=torrent_id)
    return HttpResponse(torrent.torrent_file, content_type='application/x-bittorrent')


@login_required
@user_passes_test(lambda u: u.is_superuser is True)
@json_return_method
def cache_next(request):
    bibliotik_id = request.GET['bibliotik_id']
    bibliotik_client = BibliotikClient(bibliotik_id)
    last_id = BibliotikTorrentPageCache.objects.aggregate(Max('id'))['id__max'] or 0
    next_id = last_id + 1
    response = bibliotik_client.session.get(
        BIBLIOTIK_GET_TORRENT_URL.format(next_id), allow_redirects=False)
    if response.status_code == 200:
        pass
    elif response.status_code == 302:
        location = response.headers['location']
        if location.startswith('http://bibliotik.org/log/'):
            pass
        else:
            return {'success': False, 'location': location}
    else:
        return {'success': False, 'status_code': response.status_code}
    item = BibliotikTorrentPageCache(id=next_id, status_code=response.status_code,
                                     headers=json_dumps(dict(response.headers)),
                                     body=response.text)
    item.save()
    res = {'success': True, 'id': item.id, 'status_code': item.status_code,
           'body_length': len(item.body)}
    if 'location' in response.headers:
        res['location'] = response.headers['location']
    return res
