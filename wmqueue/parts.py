import traceback

from django.contrib.auth.decorators import login_required, permission_required
from django.db.models.aggregates import Sum
from django.shortcuts import render

from WhatManager2 import manage_torrent
from WhatManager2.settings import MIN_FREE_DISK_SPACE, MIN_WHAT_RATIO
from WhatManager2.templatetags.custom_filters import filesizeformat
from WhatManager2.utils import json_return_method, html_unescape, get_artists
from home.models import DownloadLocation, LogEntry, ReplicaSet, WhatTorrent, get_what_client
from wmqueue.models import QueueItem, filter_group, filter_torrent, is_existing
from what_profile.models import WhatUserSnapshot


def get_auto_pop_ratio_delta(snapshot):
    return snapshot.uploaded / MIN_WHAT_RATIO - snapshot.downloaded


@login_required
@permission_required('wmqueue.add_queueitem', raise_exception=True)
def pop_remove(request):
    front = QueueItem.get_front()
    if not front:
        return {
            'success': False,
            'message': 'Queue is empty.'
        }
    front.delete()
    return {
        'success': True
    }


@login_required
@permission_required('wmqueue.add_queueitem', raise_exception=True)
@json_return_method
def auto_pop(request):
    front = QueueItem.get_front()
    if not front:
        LogEntry.add(request.user, 'info', 'Auto pop: queue is empty.')
        return {
            'success': False,
            'error': 'Queue is empty.'
        }
    try:
        ratio_delta = get_auto_pop_ratio_delta(WhatUserSnapshot.get_last())
    except WhatUserSnapshot.DoesNotExist:
        LogEntry.add(request.user, 'info', 'Auto pop: User profile not updated, skipping pop.')
        return {
            'success': False,
            'error': 'User profile not updated, skipping pop.'
        }
    if ratio_delta >= front.torrent_size:
        return do_pop(request)
    else:
        message = 'Auto pop: ratio delta {0} < {1}, skipping pop.'.format(
            filesizeformat(ratio_delta),
            filesizeformat(front.torrent_size)
        )
        LogEntry.add(request.user, 'info', message)
        return {
            'success': False,
            'error': 'Buffer is {0}, skipping pop.'.format(message)
        }


@login_required
@permission_required('wmqueue.add_queueitem', raise_exception=True)
@json_return_method
def do_pop(request):
    download_location = DownloadLocation.get_what_preferred()
    if download_location.free_space_percent < MIN_FREE_DISK_SPACE:
        LogEntry.add(request.user, 'error', 'Failed to add torrent. Not enough disk space.')
        return {
            'success': False,
            'error': 'Not enough free space on disk.'
        }

    front = QueueItem.get_front()
    if not front:
        return {
            'success': False,
            'message': 'Queue is empty.'
        }

    instance = ReplicaSet.get_what_master().get_preferred_instance()

    if WhatTorrent.is_downloaded(request, what_id=front.what_id):
        front.delete()
        return {
            'success': True,
            'message': 'Already added.'
        }

    try:
        m_torrent = manage_torrent.add_torrent(request, instance, download_location, front.what_id)
        m_torrent.what_torrent.added_by = request.user
        m_torrent.what_torrent.tags = 'seed project'
        m_torrent.what_torrent.save()

        front.delete()

        LogEntry.add(request.user, 'action', 'Popped {0} from queue.'.format(m_torrent))
    except Exception as ex:
        tb = traceback.format_exc()
        LogEntry.add(request.user, 'error',
                     'Tried popping what_id={0} from queue. Error: {1}'.format(front.what_id,
                                                                                str(ex)), tb)
        return {
            'success': False,
            'error': str(ex),
            'traceback': tb
        }

    return {
        'success': True
    }


@login_required
@permission_required('wmqueue.add_queueitem', raise_exception=True)
def queue_pop(request):
    data = {
        'front': QueueItem.get_front()
    }
    return render(request, 'wmqueue/part_ui/queue_pop.html', data)


@login_required
def queue_stats(request):
    ratio_delta = '-'
    try:
        ratio_delta = get_auto_pop_ratio_delta(WhatUserSnapshot.get_last())
    except (WhatUserSnapshot.DoesNotExist, IndexError):
        pass
    data = {
        'item_count': QueueItem.objects.count(),
        'total_size': QueueItem.objects.aggregate(Sum('torrent_size'))['torrent_size__sum'],
        'auto_pop_ratio_delta': ratio_delta,
    }
    return render(request, 'wmqueue/part_ui/queue_stats.html', data)


@login_required
@permission_required('wmqueue.add_queueitem', raise_exception=True)
@json_return_method
def add_artist(request, artist_name):
    what_client = get_what_client(request)
    response = what_client.request('artist', artistname=artist_name)['response']
    added = 0
    for group in response['torrentgroup']:
        if filter_group(response['name'], group):
            artist = html_unescape(response['name'])
            title = html_unescape(group['groupName'])
            release_type = group['releaseType']
            for torrent in group['torrent']:
                id = torrent['id']
                priority = filter_torrent(group, torrent)
                if priority and not is_existing(id):
                    format = torrent['format']
                    encoding = torrent['encoding']
                    torrent_size = torrent['size']
                    queue_item = QueueItem(
                        what_id=id,
                        priority=priority,
                        artist=artist,
                        title=title,
                        release_type=release_type,
                        format=format,
                        encoding=encoding,
                        torrent_size=torrent_size
                    )
                    queue_item.save()
                    added += 1
    return {
        'success': True,
        'added': added
    }


@login_required
@permission_required('wmqueue.add_queueitem', raise_exception=True)
@json_return_method
def add_collage(request, collage_id):
    what_client = get_what_client(request)
    response = what_client.request('collage', id=collage_id)['response']
    added = 0
    torrent_group_count = 0
    torrent_count = 0
    for group in response['torrentgroups']:
        if group['categoryId'] not in [1, '1']:
            continue
        artist = get_artists(group)
        title = html_unescape(group['name'])
        release_type = group['releaseType']
        for torrent in group['torrents']:
            what_id = torrent['torrentid']
            priority = filter_torrent(group, torrent)
            if priority and not is_existing(what_id):
                torrent_format = torrent['format']
                encoding = torrent['encoding']
                torrent_size = torrent['size']
                queue_item = QueueItem(
                    what_id=what_id,
                    priority=priority,
                    artist=artist,
                    title=title,
                    release_type=release_type,
                    format=torrent_format,
                    encoding=encoding,
                    torrent_size=torrent_size
                )
                queue_item.save()
                added += 1
            torrent_count += 1
        torrent_group_count += 1
    return {
        'success': True,
        'added': added,
        'groups': torrent_group_count,
        'torrents': torrent_count
    }
