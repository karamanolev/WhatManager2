# Create your views here.
from collections import defaultdict
import json
import time
import zlib
from django.contrib.auth.decorators import login_required, permission_required
from django.core.cache import cache

from django.shortcuts import render
from WhatManager2.utils import get_artists

from home.models import WhatTorrent, TransTorrent, ReplicaSet


def get_edition_name(info):
    g_info = info['group']
    t_info = info['torrent']
    if t_info['remastered']:
        points = [
            t_info['remasterYear'],
            t_info['remasterRecordLabel'],
            t_info['remasterCatalogueNumber'],
            t_info['remasterTitle'],
        ]
    else:
        points = [
            g_info['year'],
            g_info['recordLabel'],
            g_info['catalogueNumber'],
        ]
    points += [
        t_info['media'],
        'Scene' if t_info['scene'] else ''
    ]
    return ' / '.join(str(i) for i in points if i)


def get_torrent_title(info):
    points = [info['format'], info['encoding']]
    if info['format'] == 'FLAC':
        if info['hasLog']:
            points.append('Log ({0}%)'.format(info['logScore']))
        if info['hasCue']:
            points.append('Cue')
    if info['reported']:
        points.append('Reported')
    return ' / '.join(points)


def gen_group_list():
    t_torrents = TransTorrent.objects.filter(instance__in=list(
        ReplicaSet.get_what_master().transinstance_set.all()))
    t_torrents = {t.what_torrent_id: t for t in t_torrents}

    groups = defaultdict(dict)
    for t in WhatTorrent.objects.all():
        if not t.id in t_torrents:
            continue

        t_info = t.info_loads
        if t_info['group']['categoryId'] != 1:
            continue

        t_info['torrent_title'] = get_torrent_title(t_info['torrent'])

        t_d = groups[t.what_group_id]

        t_d['group'] = t_info['group']
        t_d['artists'] = get_artists(t_d['group'])

        if not 'torrents' in t_d:
            t_d['torrents'] = defaultdict(list)

        edition_name = get_edition_name(t_info)
        t_d['torrents'][edition_name].append(t_info)

    for key, value in groups.items():
        value['torrents'] = sorted(value['torrents'].items(), key=lambda x: x[0])

    return sorted(groups.values(), key=lambda x: (x['artists'], x['group']['name']))


def get_cached_or_gen():
    cache_key = TransTorrent.objects.count()
    key, value = cache.get('torrent-list', (None, None))
    if key == cache_key:
        return json.loads(zlib.decompress(value))
    else:
        data = gen_group_list()
        cache.set('torrent-list',
                  (cache_key, zlib.compress(json.dumps(data), 1)),
                  timeout=None)
        return data


@login_required
@permission_required('home.view_whattorrent', raise_exception=True)
def index(request):
    start_time = time.time()

    group_list = get_cached_or_gen()

    data = {
        'groups': group_list
    }

    print 'Compute time:', time.time() - start_time

    return render(request, 'torrent_list/index.html', data)