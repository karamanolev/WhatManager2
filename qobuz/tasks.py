import os
import os.path
from subprocess import call
import ujson

from celery import task
from django.db import connection
from mutagen.flac import FLAC
import requests

from WhatManager2.settings import WHAT_ANNOUNCE
from books import utils
from qobuz.api import get_qobuz_client
from qobuz.models import QobuzUpload, fix_filepath
from what_transcode.utils import recursive_chmod


@task(bind=True, track_started=True)
def download_album(celery_task, qobuz_album_id):
    try:
        qobuz_client = get_qobuz_client(lambda: None)
        qobuz_upload = QobuzUpload.objects.get(id=qobuz_album_id)
        assert len(qobuz_upload.album_data['tracks']['items']) == len(qobuz_upload.track_data)
        os.makedirs(qobuz_upload.temp_media_path)
        print('Downloading images')
        if qobuz_upload.album_data['image']['back']:
            download_image(qobuz_upload, qobuz_upload.album_data['image']['back'], 'back.jpg')
        download_image(qobuz_upload, qobuz_upload.album_data['image']['large'], 'folder.jpg')
        print('Download goodies')
        if 'goodies' in qobuz_upload.album_data:
            for i in range(len(qobuz_upload.album_data['goodies'])):
                download_goodie(qobuz_upload, i)
        print('Downloading tracks')
        track_number = 0
        media_number = 0
        for i, track in enumerate(qobuz_upload.album_data['tracks']['items']):
            if track['media_number'] != media_number:
                track_number = 1
                media_number = track['media_number']
            download_track(qobuz_client, qobuz_upload, i, track_number)
            track_number += 1
        print('Generating torrent')
        generate_torrents(qobuz_upload)
        print('Generating spectrals')
        os.makedirs(qobuz_upload.spectrals_path)
        for i in range(len(qobuz_upload.album_data['tracks']['items'])):
            generate_spectrals(qobuz_upload, i)
        qobuz_upload.track_data_json = ujson.dumps(qobuz_upload.track_data)
        recursive_chmod(qobuz_upload.temp_media_path, 0o777)
    finally:
        connection.close()


def download_image(qobuz_upload, url, filename):
    if url[-8:] in ('_230.jpg', '_600.jpg'):
        url = url[:-8] + '_600.jpg'
    else:
        raise Exception('Unexpected image url: ' + url)
    file_path = os.path.join(qobuz_upload.temp_media_path, filename)
    print('Downloading', url)
    response = requests.get(url)
    assert response.headers['Content-Type'] == 'image/jpeg'
    with open(file_path, 'wb') as f:
        f.write(response.content)


def generate_spectrals(qobuz_upload, i):
    track = qobuz_upload.track_data[i]
    full_dest_path = os.path.join(qobuz_upload.spectrals_path, '{0:02}.full.png'.format(i + 1))
    zoom_dest_path = os.path.join(qobuz_upload.spectrals_path, '{0:02}.zoom.png'.format(i + 1))
    args = [
        'sox', track['path'], '-n', 'remix', '1', 'spectrogram', '-x', '3000', '-y', '513', '-w',
        'Kaiser', '-S', '0:40', '-d', '0:04', '-h', '-t', '{0} Zoom'.format(track['title']),
        '-o', zoom_dest_path
    ]
    if call(args) != 0:
        raise Exception('sox returned non-zero')
    args = [
        'sox', track['path'], '-n', 'remix', '1', 'spectrogram', '-x', '3000', '-y', '513', '-w',
        'Kaiser', '-h', '-t', '{0} Full'.format(track['title']), '-o', full_dest_path
    ]
    if call(args) != 0:
        raise Exception('sox returned non-zero')


def generate_torrents(qobuz_upload):
    utils.call_mktorrent(
        qobuz_upload.temp_media_path,
        os.path.join(qobuz_upload.temp_media_path, qobuz_upload.torrent_name + '.torrent'),
        WHAT_ANNOUNCE,
        qobuz_upload.torrent_name
    )
    pass


def download_goodie(qobuz_upload, index):
    goodie = qobuz_upload.album_data['goodies'][index]
    if not goodie['original_url'].endswith('.pdf'):
        raise Exception('Weird goodie')
    goodie_path = os.path.join(qobuz_upload.temp_media_path, '{0}.pdf'.format(
        fix_filepath(goodie['description'])
    ))
    print('Downloading', goodie['original_url'])
    response = requests.get(goodie['original_url'])
    response.raise_for_status()
    assert len(response.content) > 1000
    with open(goodie_path, 'wb') as f:
        f.write(response.content)


def download_track(qobuz_client, qobuz_upload, index, track_number):
    qobuz_track = qobuz_upload.album_data['tracks']['items'][index]
    track = qobuz_upload.track_data[index]
    total_medias = qobuz_upload.album_data['tracks']['items'][-1]['media_number']
    total_tracks = sum(qobuz_track['media_number'] == t['media_number'] for t in
                       qobuz_upload.album_data['tracks']['items'])
    if total_medias > 1:
        file_name = '{0}.{1:02d}. {2}.flac'.format(
            qobuz_track['media_number'],
            track_number,
            fix_filepath(track['title'])
        )
    else:
        file_name = '{0:02d}. {1}.flac'.format(track_number, fix_filepath(track['title']))
    file_path = os.path.join(qobuz_upload.temp_media_path, file_name)
    track['path'] = file_path
    # Download
    track_info = qobuz_client.get_file_url(qobuz_track['id'], '6')
    assert track_info['mime_type'] == 'audio/flac'
    print('Downloading', track_info['url'])
    response = requests.get(track_info['url'])
    response.raise_for_status()
    assert len(response.content) > 100000
    with open(file_path, 'wb') as f:
        f.write(response.content)
    if call(['flac', '-t', file_path]) != 0:
        raise Exception('flac -t returned non-zero')
    meta_file = FLAC(file_path)
    meta_file['album'] = qobuz_upload.album_name
    meta_file['albumartist'] = qobuz_upload.artists
    meta_file['artist'] = track['artists']
    meta_file['title'] = track['title']
    meta_file['date'] = qobuz_upload.album_year
    meta_file['genre'] = qobuz_upload.album_data['genre']['name']
    meta_file['tracknumber'] = str(track_number)
    meta_file['totaltracks'] = str(total_tracks)
    meta_file['discnumber'] = str(track['media_number'])
    meta_file['totaldiscs'] = str(total_medias)
    meta_file.save()


def start_download_album(qobuz_upload):
    if qobuz_upload.download_task_id is not None:
        raise Exception('There is already a task assigned.')
    async_result = download_album.delay(qobuz_upload.id)
    qobuz_upload.download_task_id = async_result.id
    qobuz_upload.save()
