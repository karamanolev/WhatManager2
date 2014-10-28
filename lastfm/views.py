from django.contrib.auth.decorators import login_required
from django.shortcuts import render
import json
from django.http import StreamingHttpResponse
from django.views.decorators.csrf import csrf_exempt
import pylast
import time 
import from WhatManager2.settings LASTFM_API_KEY, LASTFM_API_SECRET, LASTFM_USERNAME, LASTFM_PASSWORD


lastfm_network = pylast.LastFMNetwork(api_key = LASTFM_API_KEY, api_secret =
    LASTFM_API_SECRET, username = LASTFM_USERNAME, password_hash = pylast.md5(LASTFM_PASSWORD))


@csrf_exempt
def scrobble(request):
    print 'Request'
    print vars(request)
    if request.method=='POST':
            received_json_data=json.loads(request.body)
            artist = received_json_data['artist']
            song = received_json_data['title']
            lastfm_network.scrobble(
            artist=artist, title=song, timestamp=int(time.time()))
            #received_json_data=json.loads(request.body)
            return StreamingHttpResponse('it was post request: '+str(received_json_data))
    return StreamingHttpResponse('it was GET request')
