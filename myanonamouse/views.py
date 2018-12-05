import traceback
import time

from django.contrib.auth.decorators import login_required, user_passes_test
from django.http.response import HttpResponse

from WhatManager2.utils import json_return_method
from home.models import ReplicaSet, LogEntry, TorrentAlreadyAddedException
from myanonamouse import trans_sync, manage_mam
from myanonamouse.models import MAMTorrent, MAMTransTorrent
from myanonamouse.utils import MAMClient


@login_required
@user_passes_test(lambda u: u.is_superuser is True)
@json_return_method
def sync(request):
    start_time = time.time()

    try:
        master = ReplicaSet.get_myanonamouse_master()
        trans_sync.sync_all_instances_db(master)
    except Exception as ex:
        tb = traceback.format_exc()
        LogEntry.add(request.user, 'error', 'Error syncing MyAnonaMouse master DB: {0}({1})'
                     .format(type(ex).__name__, ex), tb)
        return {
            'success': False,
            'error': str(ex),
            'traceback': tb
        }

    time_taken = time.time() - start_time
    LogEntry.add(request.user, 'info',
                 'Completed MyAnonaMouse sync in {0:.3f}s.'
                 .format(time_taken))
    return {
        'success': True
    }


@login_required
@user_passes_test(lambda u: u.is_superuser is True)
@json_return_method
def add_torrent(request, torrent_id):
    mam_client = MAMClient.get()
    try:
        m_torrent = manage_mam.add_mam_torrent(torrent_id, mam_client=mam_client)
        mam_torrent = m_torrent.mam_torrent
        LogEntry.add(request.user, 'action', 'Added {0} to {1}'
                     .format(m_torrent, m_torrent.instance))
        return {
            'success': True,
            'title': mam_torrent.title,
        }
    except TorrentAlreadyAddedException:
        mam_torrent = None
        try:
            mam_torrent = MAMTorrent.objects.get(id=torrent_id)
        except MAMTorrent.DoesNotExist:
            pass
        LogEntry.add(request.user, 'info',
                     'Tried adding MyAnonaMouse torrent_id={0}, already added.'.format(torrent_id))
        return {
            'success': False,
            'error_code': 'already_added',
            'error': 'Already added.',
            'title': (mam_torrent.title if mam_torrent
                      else '<<< Unable to find torrent >>>'),
        }
    except Exception as ex:
        tb = traceback.format_exc()
        LogEntry.add(request.user, 'error',
                     'Tried adding MyAnonaMouse torrent_id={0}. Error: {1}'
                     .format(torrent_id, str(ex)), tb)
        return {
            'success': False,
            'error': str(ex),
            'traceback': tb,
        }


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
    torrents = MAMTransTorrent.objects.filter(mam_torrent_id__in=ids)
    torrents = {t.mam_torrent_id: t for t in torrents}
    for torrent in torrents.values():
        if torrent.torrent_done < 1:
            torrent.sync_t_torrent()

    return [get_response(t_id, torrents.get(t_id)) for t_id in ids]


@login_required
@user_passes_test(lambda u: u.is_superuser is True)
def get_torrent_file(request, torrent_id):
    torrent = MAMTorrent.objects.get(id=torrent_id)
    return HttpResponse(torrent.torrent_file, content_type='application/x-bittorrent')
