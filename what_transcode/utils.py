import html.parser
import hashlib
import os
import subprocess
import time

import bencode
from mutagen.flac import FLAC
from pyquery.pyquery import PyQuery

from home.models import TransTorrent, ReplicaSet


def get_channels_number(file_path):
    return int(subprocess.check_output(['metaflac', '--show-channels', file_path]))


def get_sample_rate(file_path):
    return int(subprocess.check_output(['metaflac', '--show-sample-rate', file_path]))


def get_bit_depth(file_path):
    return int(subprocess.check_output(['metaflac', '--show-bps', file_path]))


def html_unescape(value):
    h = html.parser.HTMLParser()
    return h.unescape(value)


def fix_pathname(path):
    return ''.join(c for c in path if c not in '\/:*?"<>|')


def get_mp3_ids(what_group, what_torrent):
    res = {}
    for t in what_group['torrents']:
        if t['format'] != 'MP3':
            continue
        check_keys = ['remastered', 'media', 'remasterCatalogueNumber', 'remasterRecordLabel',
                      'remasterTitle', 'remasterYear']
        if all(t[k] == what_torrent['torrent'][k] for k in check_keys):
            if t['encoding'] == '320':
                res['320'] = t['id']
            elif t['encoding'] == 'V0 (VBR)':
                res['V0'] = t['id']
            elif t['encoding'] == 'V2 (VBR)':
                res['V2'] = t['id']
    return res


def get_trans_torrent(what_torrent):
    return TransTorrent.objects.get(
        what_torrent=what_torrent,
        instance__in=list(ReplicaSet.get_what_master().transinstance_set.all())
    )


def torrent_is_preemphasized(t_info):
    return ('pre-emphasized' in t_info['torrent']['remasterTitle'].lower() or
            'pre-emphasis' in t_info['torrent']['description'].lower())


def get_info_hash_from_data(torrent_data):
    metainfo = bencode.bdecode(torrent_data)
    info = metainfo['info']
    return hashlib.sha1(bencode.bencode(info)).hexdigest().upper()


def get_info_hash(torrent_path):
    with open(torrent_path, 'rb') as torrent_file:
        return get_info_hash_from_data(torrent_file.read())


def pthify_torrent(torrent_data):
    data = bencode.bdecode(torrent_data)
    data['info']['source'] = 'RED'
    return bencode.bencode(data)


def norm_dest_path(torrent_name, dest_path):
    len_debt = len(dest_path) - 180 + len(torrent_name) + 1  # 1 for the /
    if len_debt < 0:
        return dest_path
    filename = os.path.basename(dest_path)
    dirname = os.path.dirname(dest_path)

    new_len = len(filename) - len_debt
    if new_len < 40:
        raise Exception('Shortening the filename will make it less than 40 chars ({0}).'
                        .format(new_len))
    filename = filename[:new_len - 4 - 3] + '...' + filename[-4:]
    return os.path.join(dirname, filename)


def extract_upload_errors(html):
    pq = PyQuery(html)
    result = []
    for e in pq.find('.thin > p[style="color: red; text-align: center;"]'):
        result.append(PyQuery(e).text())
    return result


def recursive_chmod(dest_path, mode):
    os.chmod(dest_path, mode)
    for root, dirs, files in os.walk(dest_path):
        for item in dirs:
            os.chmod(os.path.join(root, item), mode)
        for item in files:
            os.chmod(os.path.join(root, item), mode)


def check_flac_tags(flac_path):
    flac = FLAC(flac_path)
    if not flac.get('artist'):
        raise Exception('Missing artist tag on {0}'.format(flac_path))
    if not flac.get('album'):
        raise Exception('Missing album tag on {0}'.format(flac_path))
    if not flac.get('title'):
        raise Exception('Missing title tag on {0}'.format(flac_path))

    track = flac.get('tracknumber') or flac.get('track')
    if type(track) in [str, str] and '/' in track:
        track = track.split('/')
    if type(track) is list:
        track = track[0]
    if not track:
        raise Exception('Missing track tag on {0}'.format(flac_path))

    disc = flac.get('discnumber') or flac.get('disc')
    if type(disc) in [str, str] and '/' in disc:
        disc = disc.split('/')
    if type(disc) is list:
        disc = disc[0]

    if disc:
        return disc, track
    else:
        return track,


def intify_tuple(t):
    r = list(t)
    for i, val in enumerate(r):
        try:
            r[i] = int(val)
        except ValueError:
            pass
    return tuple(r)


def check_directory_tags_filenames(dir_path):
    print('Check tags in ', dir_path)
    flac_tracks = []
    for child in os.listdir(dir_path):
        child_path = os.path.join(dir_path, child)
        if os.path.isfile(child_path):
            if child_path.lower().endswith('.flac'):
                flac_tracks.append((child_path, check_flac_tags(child_path)))
        elif os.path.isdir(child_path):
            check_directory_tags_filenames(child_path)

    flac_tracks = [(path, intify_tuple(track)) for path, track in flac_tracks]

    if sorted(flac_tracks, key=lambda x: x[0]) != sorted(flac_tracks, key=lambda x: x[1]):
        print(flac_tracks)
        raise Exception('Filenames and track numbers do not sort the same way')


def safe_retrieve_new_torrent(what_client, info_hash):
    for i in range(6):
        try:
            return what_client.request('torrent', hash=info_hash)['response']
        except Exception:
            print('Error retrieving new torrent, will try again in 10 sec...')
            time.sleep(10)
    return what_client.request('torrent', hash=info_hash)['response']
