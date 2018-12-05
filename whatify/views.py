import traceback

from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from WhatManager2.manage_torrent import add_torrent
from WhatManager2.utils import json_return_method
from home.models import get_what_client, ReplicaSet, DownloadLocation
from what_meta.models import WhatTorrentGroup, WhatArtist, WhatMetaFulltext
from what_transcode.utils import html_unescape
from whatify.response_gen import get_torrent_group_dict, get_torrent_groups_have, \
    get_artist_dict, get_artist_alias_dict, get_image_cache_url
from whatify.utils import get_ids_to_download


@login_required
def index(request):
    return render(request, 'whatify/index.html')


@login_required
@json_return_method
def search(request, query):
    meta_fulltext = WhatMetaFulltext.objects.only('id', 'artist', 'torrent_group')
    meta_fulltext = meta_fulltext.extra(
        where=['MATCH(`info`, `more_info`) AGAINST (%s IN BOOLEAN MODE)'], params=[query])
    meta_fulltext = meta_fulltext.extra(select={'score': 'MATCH (`info`) AGAINST (%s)'},
                                        select_params=[query])
    meta_fulltext = meta_fulltext.extra(order_by=['-score'])
    meta_fulltext = meta_fulltext.prefetch_related('artist', 'torrent_group', 'artist_alias',
                                                   'artist_alias__artist')
    meta_fulltext = meta_fulltext[:20]
    results = []
    for result in meta_fulltext:
        if result.artist:
            results.append({'type': 'artist', 'artist': get_artist_dict(result.artist)})
        elif result.torrent_group:
            results.append({
                'type': 'torrent_group',
                'torrent_group': get_torrent_group_dict(result.torrent_group)
            })
        elif result.artist_alias:
            results.append({
                'type': 'artist',
                'artist': get_artist_alias_dict(result.artist_alias)
            })
    return results


@login_required
@json_return_method
def get_torrent_group(request, group_id):
    try:
        if 'HTTP_X_REFRESH' in request.META:
            raise WhatTorrentGroup.DoesNotExist()
        torrent_group = WhatTorrentGroup.objects.get(id=group_id)
    except WhatTorrentGroup.DoesNotExist:
        what_client = get_what_client(request)
        torrent_group = WhatTorrentGroup.update_from_what(what_client, group_id)
    data = get_torrent_group_dict(torrent_group)
    data.update(get_torrent_groups_have([torrent_group.id], True)[torrent_group.id])
    return data


@login_required
@json_return_method
def download_torrent_group(request, group_id):
    if not request.user.has_perm('home.add_whattorrent'):
        return {
            'success': False,
            'error': 'You don\'t have permission to add torrents. Talk to the administrator.',
        }
    try:
        torrent_group = WhatTorrentGroup.objects.get(id=group_id)
    except WhatTorrentGroup.DoesNotExist:
        torrent_group = WhatTorrentGroup.update_from_what(get_what_client(request), group_id)
    if torrent_group.torrents_json is None:
        torrent_group = WhatTorrentGroup.update_from_what(get_what_client(request), group_id)
    ids = get_ids_to_download(torrent_group)
    try:
        instance = ReplicaSet.get_what_master().get_preferred_instance()
        download_location = DownloadLocation.get_what_preferred()
        for torrent_id in ids:
            add_torrent(request, instance, download_location, torrent_id)
    except Exception as ex:
        return {
            'success': False,
            'error': str(ex),
            'traceback': traceback.format_exc(),
        }
    return {
        'success': True,
        'added': len(ids),
    }


@login_required
@json_return_method
def get_artist(request, artist_id):
    try:
        if 'HTTP_X_REFRESH' in request.META:
            raise WhatArtist.DoesNotExist()
        artist = WhatArtist.objects.get(id=artist_id)
        if artist.is_shell:
            raise WhatArtist.DoesNotExist()
    except WhatArtist.DoesNotExist:
        artist = WhatArtist.update_from_what(get_what_client(request), artist_id)
    return get_artist_dict(artist, True)


@login_required
@json_return_method
def random_torrent_groups(request):
    count = request.GET.get('count', 10)
    torrent_group_ids = list(WhatTorrentGroup.objects.extra(select={
        'rand': 'RAND()'
    }, order_by=['rand']).values_list('id', flat=True)[:count])
    torrent_groups = WhatTorrentGroup.objects.in_bulk(torrent_group_ids)
    return [get_torrent_group_dict(g) for g in torrent_groups.values()]


@login_required
@json_return_method
def top10_torrent_groups(request):
    count = request.GET.get('count', 10)
    what_client = get_what_client(request)
    top10 = what_client.request('top10', limit=100)['response']
    group_set = set()
    results = []
    for torrent in top10[0]['results']:
        if torrent['groupId'] in group_set:
            continue
        if torrent['groupCategory'] != 1:
            continue
        group_set.add(torrent['groupId'])
        results.append({
            'id': torrent['groupId'],
            'joined_artists': html_unescape(torrent['artist']),
            'name': html_unescape(torrent['groupName']),
            'year': torrent['groupYear'],
            'wiki_image': get_image_cache_url(torrent['wikiImage']),
        })
        if len(results) == count:
            break
    torrents_have = get_torrent_groups_have(t['id'] for t in results)
    for result in results:
        result.update(torrents_have[result['id']])
    return results


@json_return_method
def search_torrent_groups(request):
    request.GET['query']
