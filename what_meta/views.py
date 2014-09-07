from django.core import serializers
from django.http.response import HttpResponse

from what_meta.models import WhatTorrentGroup


def search_torrent_groups(request, query):
    response = HttpResponse(
        serializers.serialize('json', WhatTorrentGroup.objects.filter(name__icontains=query)),
        content_type='text/json',
    )
    response['Access-Control-Allow-Origin'] = '*'
    return response
