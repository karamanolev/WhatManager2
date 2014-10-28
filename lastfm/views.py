from django.contrib.auth.decorators import login_required
from django.shortcuts import render
import json
from django.http import StreamingHttpResponse
from django.views.decorators.csrf import csrf_exempt
import pylast
import time 

# You have to have your own unique two values for API_KEY and API_SECRET
# Obtain yours from http://www.last.fm/api/account for Last.fm


lastfm_network = pylast.LastFMNetwork(api_key = API_KEY, api_secret =
    API_SECRET, username = username, password_hash = password_hash)


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
