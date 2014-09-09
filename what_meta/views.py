import json

from django.core import serializers

from django.http.response import HttpResponse

from home.models import WhatTorrent
from player.player_utils import get_playlist_files, get_metadata_dict
from what_meta.models import WhatTorrentGroup


def search_torrent_groups(request, query):
    response = HttpResponse(
        serializers.serialize('json', WhatTorrentGroup.objects.filter(name__icontains=query)),
        content_type='text/json',
    )
    response['Access-Control-Allow-Origin'] = '*'
    return response


def get_torrent_group(request, group_id):
    torrent_group = WhatTorrentGroup.objects.get(id=group_id)
    torrent = WhatTorrent.objects.filter(torrent_group=torrent_group)[0]
    data = {
        'id': torrent_group.id,
        'name': torrent_group.name,
        'wikiImage': torrent_group.wiki_image,
        'playlist': [
            {
                'id': 'what/' + str(torrent.id) + '#' + str(i),
                'url': path,
                'metadata': get_metadata_dict(path)
            }
            for i, path in enumerate(get_playlist_files('what/' + str(torrent.id))[1])
        ]
    }
    response = HttpResponse(
        json.dumps(data, indent=4),
        content_type='text/json',
    )
    response['Access-Control-Allow-Origin'] = '*'
    return response
