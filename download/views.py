import io
import os
import shutil
import zipfile
import errno

from django.contrib.auth.decorators import login_required, permission_required
from django.http.response import HttpResponse
from django.shortcuts import render, redirect
from django.template.defaultfilters import filesizeformat

from WhatManager2.utils import build_url, get_user_token, auth_username_token, attemptFixPermissions
from bibliotik.models import BibliotikTransTorrent
from home.models import TransTorrent, WhatTorrent, ReplicaSet, LogEntry
from player.player_utils import get_playlist_files


def download_zip_handler(download_filename, paths):
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_STORED, True) as zip:
        for rel_path, file in paths:
            zip.write(file, rel_path, zipfile.ZIP_STORED)
    buffer.flush()

    response = HttpResponse(content_type='application/zip')
    response['Content-Disposition'] = 'attachment; filename="' + download_filename + '"'
    response['Content-Length'] = buffer.getbuffer().nbytes

    response.write(buffer.getvalue())
    buffer.close()

    return response


@login_required
@permission_required('home.download_whattorrent', raise_exception=True)
def download_zip(request, what_id):
    t_torrent = None
    for instance in ReplicaSet.get_what_master().transinstance_set.all():
        try:
            t_torrent = TransTorrent.objects.get(instance=instance, what_torrent_id=what_id)
        except TransTorrent.DoesNotExist:
            pass
    if not t_torrent:
        return HttpResponse('Could not find that torrent.')

    torrent_file = [f for f in os.listdir(t_torrent.path) if '.torrent' in f]
    if len(torrent_file) == 1:
        torrent_file = os.path.splitext(torrent_file[0])[0]
    else:
        return HttpResponse('Not one .torrent in dir: ' + t_torrent.path)

    target_dir = os.path.join(t_torrent.path, t_torrent.torrent_name)
    torrent_files = []
    if not os.path.isdir(target_dir):
        torrent_files.append((t_torrent.torrent_name, target_dir))
    else:
        for root, rel_path, files in os.walk(target_dir):
            for file in files:
                rel_path = root.replace(target_dir, '')
                if rel_path.startswith('/') or rel_path.startswith('\\'):
                    rel_path = rel_path[1:]
                rel_path = os.path.join(rel_path, file)
                torrent_files.append((rel_path, os.path.join(root, file)))

    download_filename = '[{0}] {1}.zip'.format(what_id, torrent_file)

    response = download_zip_handler(download_filename, torrent_files)
    LogEntry.add(request.user, 'action', 'Downloaded {0} - {1}'.format(
        t_torrent, filesizeformat(response['Content-Length'])
    ))
    return response


@login_required
@permission_required('home.download_whattorrent', raise_exception=True)
def download_bibliotik_zip(request, bibliotik_id):
    b_torrent = None
    for instance in ReplicaSet.get_bibliotik_master().transinstance_set.all():
        try:
            b_torrent = BibliotikTransTorrent.objects.get(instance=instance,
                                                          bibliotik_torrent_id=bibliotik_id)
        except BibliotikTransTorrent.DoesNotExist:
            pass
    if not b_torrent:
        return HttpResponse('Could not find that torrent.')

    torrent_files = []
    for root, rel_path, files in os.walk(b_torrent.path):
        for file in files:
            assert root.find(b_torrent.path) != -1
            rel_path = root.replace(b_torrent.path, '')
            if rel_path.startswith('/') or rel_path.startswith('\\'):
                rel_path = rel_path[1:]
            rel_path = os.path.join(rel_path.encode('utf-8'), file)
            torrent_files.append((rel_path, os.path.join(root, file)))

    download_filename = '[{0}] {1}.zip'.format(bibliotik_id, b_torrent.torrent_name)

    response = download_zip_handler(download_filename, torrent_files)
    LogEntry.add(request.user, 'action', 'Downloaded {0} - {1}'
                 .format(b_torrent, filesizeformat(response['Content-Length'])))
    return response


@auth_username_token
@permission_required('home.download_whattorrent', raise_exception=True)
def download_pls(request, playlist_path):
    files = []
    playlist_name, cache_entries = get_playlist_files(playlist_path)
    for f in cache_entries:
        file_data = f.easy
        file_data['path'] = request.build_absolute_uri(build_url('player:get_file', get={
            'path': f.path,
            'username': request.user.username,
            'token': get_user_token(request.user),
        }))
        files.append(file_data)

    data = {
        'files': files
    }

    response = render(request, 'download/pls.txt', data)
    response['Content-Disposition'] = ('attachment; filename="[' +
                                       playlist_path.replace('/', '-') + '] ' +
                                       playlist_name + '.pls"')
    response['Content-Type'] = 'audio/x-scpls'
    return response

@login_required
@permission_required('home.delete_whattorrent', raise_exception=True)
def delete_torrent(request, what_id):
    t_torrent = None
    for instance in ReplicaSet.get_what_master().transinstance_set.all():
        try:
            t_torrent = TransTorrent.objects.get(instance=instance, what_torrent_id=what_id)
        except TransTorrent.DoesNotExist:
            pass
    if not t_torrent:
        return HttpResponse('Could not find that torrent.')

    path = t_torrent.path # Save this because t_torrent won't exist before rmtree is called
    WhatTorrent.objects.get(info_hash=t_torrent.info_hash).delete()
    t_torrent.instance.client.remove_torrent(t_torrent.info_hash)
    try:
        shutil.rmtree(path, onerror=attemptFixPermissions)
        return redirect('home:torrents')
    except OSError as e:
        if e.errno == errno.EPERM: # Operation not permitted
            return HttpResponse('Error removing folder "{}". Permission denied. Please remove folder '
                                'manually. The torrent and database entry has been successfully removed '
                                'from Transmission and WM.'.format(path))
        else:
            raise e
