# Create your views here.
import os

from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.staticfiles.templatetags import staticfiles
from django.http.response import StreamingHttpResponse, HttpResponse
from django.shortcuts import render, redirect
import mutagen

from WhatManager2.utils import json_return_method, auth_username_token
from home.info_holder import is_image_file
from home.models import WhatFileMetadataCache
from player.player_utils import is_allowed_file, apply_range, get_playlist_files, COVER_FILENAMES, \
    file_as_image


@login_required
@permission_required('home.download_whattorrent', raise_exception=True)
def index(request):
    playlist_files = None
    if 'playlist' in request.GET:
        playlist_name, cache_entries = get_playlist_files(request.GET['playlist'])
        playlist_files = [i.path for i in cache_entries]
    data = {
        'playlist': playlist_files
    }
    return render(request, 'player/index.html', data)


@auth_username_token
def get_file(request):
    path = request.GET['path']
    if not is_allowed_file(path):
        return HttpResponse(status=404)

    response = StreamingHttpResponse()
    response['Accept-Ranges'] = 'bytes'

    if not os.path.exists(path.encode('utf-8')):
        response.status_code = 404
        return response

    if '.flac' in path.lower():
        response['Content-Type'] = 'audio/flac'
    elif '.mp3' in path.lower():
        response['Content-Type'] = 'audio/mpeg'
    response['Content-Length'] = os.path.getsize(path.encode('utf-8'))

    if request.method == 'HEAD':
        print('head')
        return response

    file = open(path.encode('utf-8'), 'rb')
    response.streaming_content = apply_range(request, response, file)
    return response


@login_required
@permission_required('home.download_whattorrent', raise_exception=True)
@json_return_method
def metadata(request):
    path = request.GET['path']
    if not is_allowed_file(path):
        return HttpResponse(status=404)
    c = WhatFileMetadataCache()
    c.fill(path, 0)
    return c.easy


@login_required
@permission_required('home.download_whattorrent', raise_exception=True)
def album_art(request):
    path = request.GET['path']
    if not is_allowed_file(path):
        return HttpResponse(status=404)

    file = mutagen.File(path.encode('utf-8'))
    if 'APIC:' in file:
        apic = file['APIC:']
        response = HttpResponse(content=apic.data, content_type=apic.mime)
        response['Content-Length'] = len(apic.data)
        return response
    if hasattr(file, 'pictures') and file.pictures:
        pictures = [p for p in file.pictures if p.type == 3]  # Front cover
        if pictures:
            response = HttpResponse(content=pictures[0].data, content_type=pictures[0].mime)
            response['Content-Length'] = len(pictures[0].data)
            return response
    dir = os.path.dirname(path.encode('utf-8'))
    files = os.listdir(dir)
    covers = [os.path.join(dir, f) for f in files if f in COVER_FILENAMES]
    if covers:
        return file_as_image(covers[0])
    images = [os.path.join(dir, f) for f in files if is_image_file(f)]
    if len(images) == 1:
        return file_as_image(images[0])
    return redirect(staticfiles.static('player/dgplayer/resources/fallback_avatar.png'))
