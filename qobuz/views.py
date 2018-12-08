import os
import shutil
import ujson
import datetime
import time

from celery import states
from celery.result import AsyncResult
from django.contrib.auth.decorators import login_required
from django.db.transaction import atomic
from django.http.response import HttpResponse, HttpResponseNotFound
from django.shortcuts import render, redirect
from django.views.decorators.http import last_modified
import requests
from requests.exceptions import RequestException

from WhatManager2 import whatimg
from home.models import DownloadLocation, WhatTorrent
from qobuz import tasks
from qobuz.api import get_qobuz_client
from qobuz.models import NewUploadForm, QobuzUpload, EditUploadForm
from qobuz.settings import ADD_TRANSCODE_REQUEST_URL, ADD_TRANSCODE_USERNAME, ADD_TRANSCODE_PASSWORD
from what_transcode.utils import get_info_hash


@login_required
def uploads(request):
    uploads = QobuzUpload.objects.order_by('-added').all()
    data = {
        'uploads': uploads,
    }
    return render(request, 'qobuz/uploads.html', data)


@atomic
@login_required
def edit_upload(request, upload_id):
    qobuz_upload = QobuzUpload.objects.get(id=upload_id)
    if request.method == 'POST':
        form = EditUploadForm(request.POST, qobuz_upload=qobuz_upload)
        if form.is_valid():
            qobuz_upload.artists = form.cleaned_data['artists']
            qobuz_upload.album_name = form.cleaned_data['album_name']
            tracks = []
            for i, track in enumerate(qobuz_upload.track_data):
                qobuz_track = qobuz_upload.album_data['tracks']['items'][i]
                title_field = 'track_{0}_{1}_title'.format(qobuz_track['media_number'], i + 1)
                artists_field = 'track_{0}_{1}_artists'.format(qobuz_track['media_number'], i + 1)
                tracks.append({
                    'media_number': qobuz_track['media_number'],
                    'artists': form.cleaned_data[artists_field],
                    'title': form.cleaned_data[title_field],
                })
            qobuz_upload.track_data_json = ujson.dumps(tracks)
            qobuz_upload.save()
    else:
        form = EditUploadForm(qobuz_upload=qobuz_upload)
    download_error = ''
    if qobuz_upload.download_task_id:
        async_result = AsyncResult(qobuz_upload.download_task_id)
        if async_result.state == states.PENDING:
            download_status = 'Waiting to start'
        elif async_result.state == states.STARTED:
            download_status = 'Started'
        elif async_result.state == states.SUCCESS:
            download_status = 'Completed'
        elif async_result.state == states.FAILURE:
            download_status = 'Failed'
            download_error = '{0}: {1}'.format(type(async_result.result).__name__,
                                               async_result.result.message)
        else:
            download_status = 'Unknown Status'
    else:
        download_status = 'not_started'
    try:
        spectral_files = sorted(os.listdir(qobuz_upload.spectrals_path))
    except OSError:
        spectral_files = []
    try:
        cover_files = sorted([f for f in os.listdir(qobuz_upload.temp_media_path)
                              if f.endswith('.jpg')], reverse=True)
    except OSError:
        cover_files = []
    data = {
        'upload': qobuz_upload,
        'form': form,
        'download_status': download_status,
        'download_error': download_error,
        'spectral_files': spectral_files,
        'cover_files': cover_files,
    }
    return render(request, 'qobuz/edit_upload.html', data)


@login_required
def download_torrent_file(request, upload_id):
    qobuz_upload = QobuzUpload.objects.get(id=upload_id)
    file_name = qobuz_upload.torrent_name + '.torrent'
    file_path = os.path.join(qobuz_upload.temp_media_path, file_name)
    f = open(file_path, 'rb')
    response = HttpResponse(f, content_type='application/x-bittorrent')
    response['Content-Disposition'] = 'attachment; filename="' + file_name + '"'
    return response


@atomic
@login_required
def upload_cover_to_whatimg(request, upload_id):
    qobuz_upload = QobuzUpload.objects.get(id=upload_id)
    with open(os.path.join(qobuz_upload.temp_media_path, 'folder.jpg'), 'rb') as f:
        data = f.read()
    qobuz_upload.what_img_cover = whatimg.upload_image_from_memory('4460', data)
    qobuz_upload.save()
    return redirect(edit_upload, upload_id)


def _add_to_wm_transcode(what_id):
    print('Adding {0} to wm'.format(what_id))
    post_data = {
        'what_id': what_id,
    }
    response = requests.post(ADD_TRANSCODE_REQUEST_URL, data=post_data,
                             auth=(ADD_TRANSCODE_USERNAME, ADD_TRANSCODE_PASSWORD))
    response_json = response.json()
    if response_json['message'] != 'Request added.':
        raise Exception('Cannot add {0} to wm: {1}'.format(what_id, response_json['message']))


def add_to_wm_transcode(what_id):
    for i in range(2):
        try:
            _add_to_wm_transcode(what_id)
            return
        except Exception:
            print('Error adding to wm, trying again in 2 sec...')
            time.sleep(3)
    _add_to_wm_transcode(what_id)


@login_required
def start_seeding(request, upload_id):
    qobuz_upload = QobuzUpload.objects.get(id=upload_id)
    dest_upload_dir = DownloadLocation.get_what_preferred().path
    torrent_file_path = os.path.join(qobuz_upload.temp_media_path,
                                     qobuz_upload.torrent_name + '.torrent')
    info_hash = get_info_hash(torrent_file_path)
    what_torrent = WhatTorrent.get_or_create(request, info_hash=info_hash)
    qobuz_upload.what_torrent = what_torrent
    qobuz_upload.save()
    dest_path = os.path.join(dest_upload_dir, str(what_torrent.id))
    shutil.rmtree(qobuz_upload.spectrals_path)
    os.remove(torrent_file_path)
    try:
        os.makedirs(dest_path)
    except OSError:
        raise Exception('Dest torrent directory already exists.')
    os.chmod(dest_path, 0o777)
    shutil.move(qobuz_upload.temp_media_path, dest_path)
    add_to_wm_transcode(str(what_torrent.id))
    return redirect(edit_upload, upload_id)


def get_image_last_modified(prop):
    def inner(request, upload_id):
        try:
            qobuz_upload = QobuzUpload.objects.get(id=upload_id)
            path = os.path.join(getattr(qobuz_upload, prop), os.path.basename(request.GET['path']))
            s = os.path.getmtime(path)
            return datetime.datetime.utcfromtimestamp(s)
        except Exception:
            return None

    return inner


@last_modified(get_image_last_modified('spectrals_path'))
def view_spectral(request, upload_id):
    try:
        qobuz_upload = QobuzUpload.objects.get(id=upload_id)
        path = os.path.join(qobuz_upload.spectrals_path, os.path.basename(request.GET['path']))
        f = open(path, 'rb')
        return HttpResponse(f, content_type='image/jpeg')
    except Exception:
        return HttpResponseNotFound()


@login_required
@last_modified(get_image_last_modified('temp_media_path'))
def view_cover(request, upload_id):
    qobuz_upload = QobuzUpload.objects.get(id=upload_id)
    path = os.path.join(qobuz_upload.temp_media_path, os.path.basename(request.GET['path']))
    f = open(path, 'rb')
    return HttpResponse(f, content_type='image/jpeg')


@atomic
@login_required
def start_download_album(request, upload_id):
    qobuz_upload = QobuzUpload.objects.get(id=upload_id)
    if qobuz_upload.download_task_id is not None:
        qobuz_upload.download_task_id = None
    tasks.start_download_album(qobuz_upload)
    return redirect(edit_upload, upload_id)


@atomic
@login_required
def new_upload(request):
    if request.method == 'POST':
        form = NewUploadForm(request.POST)
        if form.is_valid():
            qobuz = get_qobuz_client(request)
            album_id = form.cleaned_data['album_id']
            try:
                album = qobuz.call('album/get', {'album_id': album_id})
                qobuz_upload = QobuzUpload(
                    qobuz_album_id=album_id,
                    album_data_json=ujson.dumps(album),
                )
                qobuz_upload.populate_fields()
                qobuz_upload.save()
                return redirect(edit_upload, qobuz_upload.id)
            except RequestException:
                form.add_error('album_id', 'Cannot fetch Qobuz album')
    else:
        form = NewUploadForm()
    data = {
        'form': form,
    }
    return render(request, 'qobuz/new_upload.html', data)

