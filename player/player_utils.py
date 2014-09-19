import mimetypes
import os

from django.http.response import HttpResponse
import mutagen

from WhatManager2.utils import wm_str

from home.models import WhatTorrent, DownloadLocation


ALLOWED_EXTS = ['.mp3', '.flac']

COVER_FILENAMES = ['cover.jpg', 'cover.jpeg', 'folder.jpg', 'folder.jpeg']


def is_allowed_ext(file):
    return any(file.lower().endswith(e) for e in ALLOWED_EXTS)


def is_allowed_file(file):
    allowed_dirs = list(DownloadLocation.objects.values_list('path', flat=True))
    file = os.path.realpath(file.encode('utf-8')).decode('utf-8')
    if not any(file.startswith(d) for d in allowed_dirs):
        return False
    if not is_allowed_ext(file):
        return False
    return True


def yield_file(file, b_from, b_to):
    file.seek(b_from)
    while b_from < b_to:
        part = file.read(min(b_to - b_from, 1024 * 1024))
        b_from += len(part)
        yield part
    file.close()


def apply_range(request, response, file):
    file.seek(0, 2)
    file_length = file.tell()

    http_range = request.META.get('HTTP_RANGE')
    if http_range:
        if http_range.startswith('bytes='):
            http_range = http_range[len('bytes='):]
        if ',' in http_range:
            response.status_code = '416'
            return ''
        http_range = http_range.split('-')
        if len(http_range) != 2:
            response.status_code = '416'
            return ''
        if len(http_range[0]) == 0 or int(http_range[0]) < 0:
            http_range[0] = 0
        if len(http_range[1]) == 0 or int(http_range[1]) >= file_length:
            http_range[1] = file_length - 1
        http_range = [int(i) for i in http_range]

        response.status_code = 206
        response['Content-Range'] = 'bytes {0}-{1}/{2}'.format(http_range[0], http_range[1],
                                                               file_length)
        response['Content-Length'] = http_range[1] - http_range[0] + 1
        return yield_file(file, http_range[0], http_range[1] + 1)

    return yield_file(file, 0, file_length)


def get_what_playlist_files(what_torrent, trans_torrent):
    path = trans_torrent.path
    files = []
    for dirpath, dirnames, filenames in os.walk(path.encode('utf-8')):
        files += [os.path.join(dirpath, f) for f in filenames if is_allowed_ext(f)]
    files.sort()
    playlist_name = what_torrent.joined_artists + ' - ' + what_torrent.info_title
    return playlist_name, files


def get_playlist_files(playlist):
    if playlist.startswith('what/'):
        what_id = int(playlist[len('what/'):])
        what_torrent = WhatTorrent.objects.get(id=what_id)
        trans_torrent = what_torrent.master_trans_torrent
        return get_what_playlist_files(what_torrent, trans_torrent)


def file_as_image(path):
    response = HttpResponse(content_type=mimetypes.guess_type(path))
    with open(path, 'rb') as cover_file:
        response.content = cover_file.read()
        response['Content-Length'] = len(response.content)
    return response


def get_metadata_dict(path):
    meta_file = mutagen.File(wm_str(path), easy=True)

    data = {
        'artist': '',
        'album': '',
        'title': '',
        'duration': meta_file.info.length,
    }
    if 'albumartist' in meta_file and meta_file['albumartist'] and meta_file['albumartist'][0]:
        data['artist'] = meta_file['albumartist'][0]
    if 'artist' in meta_file and meta_file['artist'] and meta_file['artist'][0]:
        data['artist'] = meta_file['artist'][0]
    if 'performer' in meta_file and meta_file['performer'] and meta_file['performer'][0]:
        data['artist'] = meta_file['performer'][0]

    if 'album' in meta_file and meta_file['album']:
        data['album'] = meta_file['album'][0]
    if 'title' in meta_file and meta_file['title']:
        data['title'] = meta_file['title'][0]

    return data
