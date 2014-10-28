import json
from django.http import StreamingHttpResponse
from django.views.decorators.csrf import csrf_protect
import pylast
import time
from WhatManager2.settings import LASTFM_API_KEY, LASTFM_API_SECRET, \
    LASTFM_USERNAME, LASTFM_PASSWORD

if "" not in (LASTFM_API_KEY, LASTFM_API_SECRET, LASTFM_USERNAME, LASTFM_PASSWORD):
    lastfm_network = pylast.LastFMNetwork(api_key=LASTFM_API_KEY,
                                          api_secret=LASTFM_API_SECRET,
                                          username=LASTFM_USERNAME,
                                          password_hash=pylast.md5(LASTFM_PASSWORD))
else:
    lastfm_network = None


@csrf_protect
def scrobble(request):
    if request.method == 'POST' and lastfm_network is not None:
            received_json_data = json.loads(request.body)
            artist = received_json_data['artist']
            song = received_json_data['title']
            lastfm_network.scrobble(artist=artist,
                                    title=song,
                                    timestamp=int(time.time()))
            return StreamingHttpResponse('Scrobbled')
    return StreamingHttpResponse('Did not scrobble. It was GET request or no last.fm setup')
