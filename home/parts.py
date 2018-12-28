from collections import defaultdict
import traceback

from django.contrib.auth.decorators import login_required, permission_required
from django.shortcuts import render

from WhatManager2.utils import get_user_token
import bibliotik.utils
from bibliotik.models import BibliotikTransTorrent
from home.models import WhatTorrent, WhatFulltext, ReplicaSet, LogEntry, TransTorrent
import WhatManager2.checks
from what_profile.models import WhatUserSnapshot


@permission_required('home.run_checks')
def checks(request):
    try:
        data = WhatManager2.checks.run_checks()
    except Exception:
        tb = traceback.format_exc()
        data = {
            'traceback': tb
        }
    return render(request, 'home/part_ui/checks.html', data)


@login_required
@permission_required('home.view_whattorrent')
def downloading(request):
    downloading = []
    for m_torrent in TransTorrent.objects.filter(
            instance__in=ReplicaSet.get_what_master().transinstance_set.all(),
            torrent_done__lt=1).prefetch_related('what_torrent'):
        m_torrent.sync_t_torrent()
        downloading.append(m_torrent)
    for b_torrent in BibliotikTransTorrent.objects.filter(
            instance__in=ReplicaSet.get_bibliotik_master().transinstance_set.all(),
            torrent_done__lt=1
    ).prefetch_related('bibliotik_torrent'):
        b_torrent.sync_t_torrent()
        downloading.append(b_torrent)
    downloading.sort(key=lambda t: t.torrent_date_added)
    data = {
        'torrents': downloading
    }
    return render(request, 'home/part_ui/downloading.html', data)


@login_required
@permission_required('home.view_whattorrent')
def recently_downloaded(request):
    count = 40
    recent = []
    for instance in ReplicaSet.get_what_master().transinstance_set.all():
        torrents = instance.transtorrent_set.filter(torrent_done=1)
        torrents = torrents.order_by('-torrent_date_added')[:count]
        for t in torrents:
            t.playlist_name = 'what/{0}'.format(t.what_torrent_id)
        recent.extend(torrents)
    for instance in ReplicaSet.get_bibliotik_master().transinstance_set.all():
        bibliotik_torrents = instance.bibliotiktranstorrent_set.filter(torrent_done=1)
        bibliotik_torrents = bibliotik_torrents.order_by('-torrent_date_added')[:count]
        recent.extend(bibliotik_torrents)
    recent.sort(key=lambda lt: lt.torrent_date_added, reverse=True)
    recent = recent[:count]

    data = {
        'token': get_user_token(request.user),
        'torrents': recent,
    }
    return render(request, 'home/part_ui/recently_downloaded.html', data)


# Permission checks are inside function
@login_required
def recent_log(request):
    if request.user.has_perm('home.view_logentry'):
        types = request.POST['log_types'].split(',')
        entry_count = int(request.POST['count'])

        entries = LogEntry.objects.order_by('-datetime')
        entries = entries.filter(type__in=types)
        entries = entries[:entry_count]
        data = {
            'log_entries': entries
        }
    else:
        data = {
            'log_entries': [
                {
                    'type': 'info',
                    'message': 'You don\'t have permission to view logs.',
                }
            ]
        }
    return render(request, 'home/part_ui/recent_log.html', data)


@login_required
@permission_required('home.view_whattorrent')
def search_torrents(request):
    query = request.POST.get('query') or request.GET.get('query')
    query = ' '.join('+' + i for i in query.split())

    w_fulltext = WhatFulltext.objects.only('id').all()
    w_fulltext = w_fulltext.extra(where=['MATCH(`info`, `more_info`) AGAINST (%s IN BOOLEAN MODE)'],
                                  params=[query])
    w_fulltext = w_fulltext.extra(select={'score': 'MATCH(`info`) AGAINST (%s)'},
                                  select_params=[query])
    w_fulltext = w_fulltext.extra(order_by=['-score'])

    w_torrents_dict = WhatTorrent.objects.in_bulk([w.id for w in w_fulltext])
    w_torrents = list()
    for i in w_fulltext:
        w_torrent = w_torrents_dict[i.id]
        w_torrent.score = i.score
        w_torrents.append(w_torrent)

    b_torrents = bibliotik.utils.search_torrents(query)

    for t in w_torrents:
        t.playlist_name = 'what/{0}'.format(t.id)

    torrents = w_torrents + b_torrents
    torrents.sort(key=lambda torrent: torrent.score, reverse=True)

    data = {
        'token': get_user_token(request.user),
        'torrents': torrents,
    }
    res = render(request, 'home/part_ui/search_torrents.html', data)
    return res


@login_required
@permission_required('home.view_whattorrent')
def error_torrents(request):
    error_torrents = []
    error_torrents.extend(TransTorrent.objects.filter(
        instance__in=ReplicaSet.get_what_master().transinstance_set.all()
    ).exclude(torrent_error=0).prefetch_related('what_torrent'))
    error_torrents.extend(BibliotikTransTorrent.objects.filter(
        instance__in=ReplicaSet.get_bibliotik_master().transinstance_set.all()
    ).exclude(torrent_error=0).prefetch_related('bibliotik_torrent'))
    data = {
        'torrents': error_torrents
    }
    return render(request, 'home/part_ui/error_torrents.html', data)


@login_required
def torrent_stats(request):
    what_buffer = 0
    try:
        what_buffer = WhatUserSnapshot.get_last().buffer_105
    except WhatUserSnapshot.DoesNotExist:
        pass
    data = {
        'master': ReplicaSet.get_what_master(),
        'buffer': what_buffer,
    }
    return render(request, 'home/part_ui/torrent_stats.html', data)


# Permission checks are inside template
@login_required
def stats(request):
    stats = list()
    for replica_set in ReplicaSet.objects.filter(name='master'):
        instance_stats = list()
        set_stats = defaultdict(lambda: 0)
        for instance in replica_set.transinstance_set.all():
            istats = instance.client.session_stats()
            istats.instance_name = instance.name
            instance_stats.append(istats)

            set_stats['activeTorrentCount'] += istats.activeTorrentCount
            set_stats['totalUploadedBytes'] += istats.cumulative_stats['uploadedBytes']
            set_stats['totalDownloadedBytes'] += istats.cumulative_stats['downloadedBytes']
            set_stats['downloadedBytes'] += istats.current_stats['downloadedBytes']
            set_stats['uploadedBytes'] += istats.current_stats['uploadedBytes']
            set_stats['uploadSpeed'] += istats.uploadSpeed
            set_stats['downloadSpeed'] += istats.downloadSpeed
            set_stats['totalSecondsActive'] = max(set_stats['totalSecondsActive'],
                                                  istats.cumulative_stats['secondsActive'])
            set_stats['secondsActive'] = max(set_stats['secondsActive'],
                                             istats.current_stats['secondsActive'])
        stats.append({
            'zone': replica_set.zone,
            'set': set_stats,
            'instances': instance_stats,
        })
    data = {
        'stats': stats
    }
    return render(request, 'home/part_ui/stats.html', data)
