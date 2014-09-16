from home.models import WhatTorrent


def extract(torrent):
    t = type(torrent)
    if t is dict:
        return torrent['media'], torrent['format']
    elif t is WhatTorrent:
        return torrent.info_media, torrent.info_format


def filter_torrent(a):
    _, a_format = extract(a)
    if a_format == 'FLAC':
        return True
    return False


def compare_torrents(a, b):
    a_media, a_format = extract(a)
    b_media, b_format = extract(b)
    if a_format == 'MP3' and b_format != 'MP3':
        return -1
    if a_format != 'MP3' and b_format == 'MP3':
        return 1
    if a_media == 'WEB' and b_media != 'WEB':
        return -1
    if a_media != 'WEB' and b_media == 'WEB':
        return 1
    if a_media == 'CD' and b_media != 'CD':
        return -1
    if a_media != 'CD' and b_media == 'CD':
        return 1
    return 0


def sort_filter_torrents(torrents):
    torrents = [t for t in torrents if filter_torrent(t)]
    torrents.sort(cmp=compare_torrents)
    return torrents
