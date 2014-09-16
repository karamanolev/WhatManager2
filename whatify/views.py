from django.shortcuts import render

from WhatManager2.utils import json_return_method
from home.models import get_what_client
from what_meta.models import WhatTorrentGroup, WhatArtist, WhatMetaFulltext
from what_meta.utils import get_torrent_group_dict, get_torrent_group_playlist_or_have, \
    get_artist_dict, get_artist_alias_dict


def index(request):
    return render(request, 'whatify/index.html')


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
    data.update(get_torrent_group_playlist_or_have(torrent_group))
    return data


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
