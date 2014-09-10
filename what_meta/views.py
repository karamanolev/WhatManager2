import json

from django.core.urlresolvers import reverse

from django.http.response import HttpResponse
from django.utils.http import urlquote

from home.models import WhatTorrent
from player.player_utils import get_playlist_files, get_metadata_dict
from what_meta.models import WhatTorrentGroup


def get_torrent_group_dict(torrent_group):
    return {
        'id': torrent_group.id,
        'name': torrent_group.name,
        'wikiImage': torrent_group.wiki_image,
    }


def search_torrent_groups(request, query):
    response = HttpResponse(
        json.dumps([get_torrent_group_dict(group) for group in
                    WhatTorrentGroup.objects.filter(name__icontains=query)]),
        content_type='text/json',
    )
    response['Access-Control-Allow-Origin'] = '*'
    return response


def get_torrent_group(request, group_id):
    torrent_group = WhatTorrentGroup.objects.get(id=group_id)
    torrent = WhatTorrent.objects.filter(torrent_group=torrent_group)[0]
    data = get_torrent_group_dict(torrent_group)
    data.update({
        'playlist': [
            {
                'id': 'what/' + str(torrent.id) + '#' + str(i),
                'url': reverse('player.views.get_file') + '?path=' + urlquote(path),
                'metadata': get_metadata_dict(path)
            }
            for i, path in enumerate(get_playlist_files('what/' + str(torrent.id))[1])
        ]
    })
    response = HttpResponse(
        json.dumps(data, indent=4),
        content_type='text/json',
    )
    response['Access-Control-Allow-Origin'] = '*'
    return response
