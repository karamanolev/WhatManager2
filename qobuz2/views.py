import os
import os.path
import datetime

from celery import states
from celery.result import AsyncResult
from django.contrib.auth.decorators import login_required
from django.db.transaction import atomic
from django.http.response import HttpResponse, HttpResponseNotFound
from django.shortcuts import render, redirect
from django.views.decorators.http import last_modified

from WhatManager2.management.commands import import_external_what_torrent
from WhatManager2.settings import WHAT_ANNOUNCE, WHATIMG_USERNAME, WHATIMG_PASSWORD
from home.info_holder import WHAT_RELEASE_TYPES
from home.models import RequestException, get_what_client, WhatTorrent
from qiller.upload import QillerUpload
from qiller.what_upload import MissingImageException
from qobuz2 import tasks
from qobuz2.models import QobuzUpload, get_qobuz_client, EditUploadForm, EditTracksFormSet, \
    NewUploadForm, EditArtistsFormSet, get_tidal_client
from qobuz2.settings import WHATIMG_QOBUZ_ALBUM_ID
from qobuz2.utils import get_temp_dir, title
from what_transcode.utils import get_info_hash
from what_transcode.views import run_request_transcode


STATE_DONE = 1001

state_data = {
    'STATE_INITIALIZED': QillerUpload.STATE_INITIALIZED,
    'STATE_DOWNLOADED': QillerUpload.STATE_DOWNLOADED,
    'STATE_PREPARED': QillerUpload.STATE_PREPARED,
    'STATE_TORRENT_CREATED': QillerUpload.STATE_TORRENT_CREATED,
    'STATE_UPLOADED_WHAT': QillerUpload.STATE_UPLOADED_WHAT,
    'STATE_DONE': STATE_DONE,
}

reverse_state_data = {i[1]: i[0] for i in list(state_data.items())}


def get_image_files(qiller):
    return [i.temp_filename for i in qiller.metadata.images]


def get_spectral_files(qiller):
    spectrals_dir = os.path.join(get_temp_dir(qiller.metadata.id), 'spectrals')
    try:
        return os.listdir(spectrals_dir)
    except OSError:
        return []


def get_image_last_modified(subpath):
    def inner(request, upload_id):
        try:
            qobuz_upload = QobuzUpload.objects.get(id=upload_id)
            dest_path = os.path.join(get_temp_dir(qobuz_upload.upload.metadata.id), subpath,
                                     os.path.basename(request.GET['path']))
            s = os.path.getmtime(dest_path)
            return datetime.datetime.utcfromtimestamp(s)
        except Exception:
            raise
            return None

    return inner


@last_modified(get_image_last_modified('spectrals'))
def view_spectral(request, upload_id):
    try:
        qobuz_upload = QobuzUpload.objects.get(id=upload_id)
        dest_path = os.path.join(get_temp_dir(qobuz_upload.upload.metadata.id), 'spectrals',
                                 os.path.basename(request.GET['path']))
        f = open(dest_path, 'rb')
        return HttpResponse(f, content_type='image/png')
    except Exception:
        return HttpResponseNotFound()


@last_modified(get_image_last_modified(''))
def view_cover(request, upload_id):
    try:
        qobuz_upload = QobuzUpload.objects.get(id=upload_id)
        dest_path = os.path.join(get_temp_dir(qobuz_upload.upload.metadata.id),
                                 os.path.basename(request.GET['path']))
        f = open(dest_path, 'rb')
        return HttpResponse(f, content_type='image/jpeg')
    except Exception:
        return HttpResponseNotFound()


@login_required
def index(request):
    uploads = QobuzUpload.objects.order_by('-added').all()
    data = {
        'uploads': uploads,
    }
    return render(request, 'qobuz2/uploads.html', data)


@atomic
@login_required
def new_upload(request):
    if request.method == 'POST':
        form = NewUploadForm(request.POST)
        if form.is_valid():
            album_id = form.cleaned_data['album_id']
            try:
                QobuzUpload.objects.get(qobuz_album_id=album_id)
                form.add_error('album_id', 'Already in the upload database')
            except QobuzUpload.DoesNotExist:
                try:
                    temp_dir = get_temp_dir(album_id)
                    qiller = QillerUpload(temp_dir)
                    if 'Qobuz' in request.POST:
                        qobuz = get_qobuz_client(request)
                        qiller.load_from_qobuz(qobuz, temp_dir, album_id)
                    elif 'Tidal' in request.POST:
                        tidal = get_tidal_client(request)
                        qiller.load_from_tidal(tidal, temp_dir, album_id)
                    upload = QobuzUpload(state=qiller.state)
                    upload.set_upload(qiller)
                    upload.save()
                    os.chmod(temp_dir, 0o777)
                    return redirect('qobuz2:edit_upload', upload.id)
                except RequestException:
                    form.add_error('album_id', 'Cannot fetch Qobuz album')
    else:
        form = NewUploadForm(initial={
            'album_id': request.GET.get('id', '')
        })
    data = {
        'form': form,
    }
    return render(request, 'qobuz2/new_upload.html', data)


@login_required
def edit_upload(request, upload_id):
    upload = QobuzUpload.objects.get(id=upload_id)
    if upload.state in [QillerUpload.STATE_INITIALIZED, QillerUpload.STATE_DOWNLOADED]:
        return edit_upload_metadata(request, upload)
    elif upload.state == QillerUpload.STATE_PREPARED:
        return edit_upload_prepared(request, upload)
    elif upload.state == QillerUpload.STATE_TORRENT_CREATED:
        return edit_upload_whatcd(request, upload)
    elif upload.state == STATE_DONE:
        return redirect('qobuz2:index')


@atomic
@login_required
def upload_cover(request, upload_id):
    upload = QobuzUpload.objects.get(id=upload_id)
    temp_dir = get_temp_dir(upload.upload.metadata.id)
    qiller = upload.upload
    do_upload_cover(upload, temp_dir, qiller)
    return redirect('qobuz2:edit_upload', upload_id)


def do_upload_cover(upload, temp_dir, qiller):
    qiller.upload_cover(temp_dir, WHATIMG_USERNAME, WHATIMG_PASSWORD,
                        WHATIMG_QOBUZ_ALBUM_ID)
    upload.set_upload(qiller)
    upload.save()


def edit_upload_whatcd(request, upload):
    if request.method == 'POST':
        what_client = get_what_client(request)
        temp_dir = get_temp_dir(upload.upload.metadata.id)
        if request.GET['type'] == 'existing':
            group_id = request.POST['group_id']
            assert group_id
            if 'subgroup' in request.POST:
                upload.upload.upload_to_what(what_client, temp_dir, 'upload_in_subgroup',
                                             [group_id, None])
            elif 'original' in request.POST:
                upload.upload.upload_to_what(what_client, temp_dir, 'upload_in_original_release',
                                             [group_id])
            elif 'with_torrent' in request.POST:
                with_id = request.POST['with_id']
                assert with_id
                upload.upload.upload_to_what(
                    what_client, temp_dir, 'upload_in_subgroup', [group_id, with_id])
            else:
                raise Exception('Unknown button clicked')
        elif request.GET['type'] == 'new':
            release_type_id = request.POST['release_type']
            release_tags = request.POST['tags']
            assert release_type_id
            assert release_tags
            qiller = upload.upload

            def do_upload():
                kwargs = dict()
                if 'force_artists' in request.POST:
                    kwargs['force_artists'] = True
                if request.POST['original_year']:
                    kwargs['remaster'] = True
                    kwargs['original_year'] = request.POST['original_year']
                qiller.upload_to_what(
                    what_client, temp_dir, 'upload_new_group',
                    [release_type_id, release_tags], kwargs
                )
                upload.set_upload(qiller)
                upload.save()

            try:
                do_upload()
            except MissingImageException:
                do_upload_cover(upload, temp_dir, qiller)
                do_upload()
        else:
            raise Exception('Unknown type')
        return redirect('qobuz2:seed_upload', upload.id)
    data = {
        'upload': upload,
        'spectrals': get_spectral_files(upload.upload),
        'release_types': WHAT_RELEASE_TYPES,
    }
    return render(request, 'qobuz2/upload_whatcd.html', data)


@atomic
@login_required
def seed_upload(request, upload_id):
    qobuz_upload = QobuzUpload.objects.get(id=upload_id)
    temp_dir = get_temp_dir(qobuz_upload.upload.metadata.id)
    torrent_path = os.path.join(temp_dir, qobuz_upload.upload.metadata.torrent_name + '.torrent')
    assert os.path.isfile(torrent_path)
    info_hash = get_info_hash(torrent_path)
    what_torrent = WhatTorrent.get_or_create(request, info_hash=info_hash)
    command = import_external_what_torrent.Command()
    command.handle(data_dir=temp_dir, torrent_file=torrent_path, base_dir=False)
    try:
        run_request_transcode(request, what_torrent.id)
    except Exception:
        pass
    qiller = qobuz_upload.upload
    qiller.state = STATE_DONE
    qobuz_upload.set_upload(qiller)
    qobuz_upload.save()
    return redirect('qobuz2:edit_upload', upload_id)


def edit_upload_prepared(request, upload):
    data = {
        'upload': upload,
        'spectrals': get_spectral_files(upload.upload),
    }
    return render(request, 'qobuz2/pre_upload.html', data)


def edit_upload_metadata(request, upload):
    qiller = upload.upload
    metadata = qiller.metadata
    if request.method == 'POST':
        form = EditUploadForm(request.POST, metadata=qiller.metadata)
        tracks_formset = EditTracksFormSet(request.POST, prefix='tracks', metadata=metadata)
        artists_formset = EditArtistsFormSet(request.POST, prefix='artists', metadata=metadata)
        if form.is_valid() and artists_formset.is_valid() and tracks_formset.is_valid():
            metadata.joined_artists = form.cleaned_data['joined_artists']
            metadata.title = form.cleaned_data['title']
            metadata.label = form.cleaned_data['label']
            metadata.year = form.cleaned_data['year']
            metadata.genre = form.cleaned_data['genre']
            assert len(tracks_formset.cleaned_data) == len(metadata.tracks)
            for i, track_info in enumerate(tracks_formset.cleaned_data):
                metadata.tracks[i].joined_artists = track_info['joined_artists']
                metadata.tracks[i].title = track_info['title']
                metadata.tracks[i].track_number = track_info['track_number']
                metadata.tracks[i].media_number = track_info['media_number']
            assert len(artists_formset.cleaned_data) == len(metadata.artists)
            for i, artist_info in enumerate(artists_formset.cleaned_data):
                metadata.artists[i].name = artist_info['name']
                metadata.artists[i].artist_type = int(artist_info['artist_type'])
            upload.set_upload(qiller)
            upload.save()
    else:
        form = EditUploadForm(metadata=qiller.metadata)
        tracks_formset = EditTracksFormSet(prefix='tracks', metadata=qiller.metadata)
        artists_formset = EditArtistsFormSet(prefix='artists', metadata=qiller.metadata)
    data = {
        'upload': upload,
        'form': form,
        'tracks_formset': tracks_formset,
        'artists_formset': artists_formset,
        'spectrals': get_spectral_files(upload.upload),
        'images': get_image_files(upload.upload),
    }
    if upload.download_task_id:
        async_result = AsyncResult(upload.download_task_id)
        if async_result.state == states.PENDING:
            data['status'] = 'pending'
        elif async_result.state == states.STARTED:
            data['status'] = 'started'
        elif async_result.state == states.FAILURE:
            data['status'] = 'failed'
            data['error'] = '{0}: {1}'.format(type(async_result.result).__name__,
                                              async_result.result.message)
        else:
            data['status'] = 'unknown'
    data.update(state_data)
    return render(request, 'qobuz2/edit_upload.html', data)


@atomic
@login_required
def title_case(request, upload_id):
    qobuz_upload = QobuzUpload.objects.get(id=upload_id)
    assert qobuz_upload.state in [QillerUpload.STATE_INITIALIZED,
                                  QillerUpload.STATE_DOWNLOADED]
    qiller = qobuz_upload.upload
    metadata = qiller.metadata
    metadata.joined_artists = title(metadata.joined_artists)
    metadata.title = title(metadata.title)
    metadata.label = title(metadata.label)
    for artist in metadata.artists:
        artist.name = title(artist.name)
    for track in metadata.tracks:
        track.joined_artists = title(track.joined_artists)
        track.title = title(track.title)

    qobuz_upload.set_upload(qiller)
    qobuz_upload.save()
    return redirect('qobuz2:edit_upload', upload_id)


@atomic
@login_required
def prepare(request, upload_id):
    qobuz_upload = QobuzUpload.objects.get(id=upload_id)
    qiller = qobuz_upload.upload
    qiller.prepare(get_temp_dir(qiller.metadata.id))
    qobuz_upload.set_upload(qiller)
    qobuz_upload.save()
    return redirect('qobuz2:edit_upload', upload_id)


@atomic
@login_required
def make_torrent(request, upload_id):
    qobuz_upload = QobuzUpload.objects.get(id=upload_id)
    qiller = qobuz_upload.upload
    qiller.make_torrent(get_temp_dir(qiller.metadata.id), WHAT_ANNOUNCE)
    qobuz_upload.set_upload(qiller)
    qobuz_upload.save()
    return redirect('qobuz2:edit_upload', upload_id)


@atomic
@login_required
def start_download(request, upload_id):
    qobuz_upload = QobuzUpload.objects.get(id=upload_id)
    if qobuz_upload.download_task_id is not None:
        qobuz_upload.download_task_id = None
    tasks.start_qiller_download(qobuz_upload)
    return redirect('qobuz2:edit_upload', upload_id)


@atomic
@login_required
def find_replace(request, upload_id):
    assert request.method == 'POST'
    qobuz_upload = QobuzUpload.objects.get(id=upload_id)
    str_find = request.POST['find']
    str_replace = request.POST['replace']
    qiller = qobuz_upload.upload
    for track in qiller.metadata.tracks:
        track.joined_artists = track.joined_artists.replace(str_find, str_replace).strip()
        track.title = track.title.replace(str_find, str_replace).strip()
    qobuz_upload.set_upload(qiller)
    qobuz_upload.save()
    return redirect('qobuz2:edit_upload', upload_id)
