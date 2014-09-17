def extended_artists_to_music_info(extended_artists):
    return {
        'musicInfo': {
            'artists': extended_artists['1'] or [],
            'with': extended_artists['2'] or [],
            'remixedBy': extended_artists['3'] or [],
            'composers': extended_artists['4'] or [],
            'conductor': extended_artists['5'] or [],
            'dj': extended_artists['6'] or [],
            'producer': extended_artists['7'] or [],
        }
    }


# Add some preferences here
def get_ids_to_download(torrent_group):
    ids = []
    for torrent in torrent_group.torrents:
        if torrent['format'].lower() != 'flac':
            continue
        if torrent['media'].lower() not in ['cd', 'web']:
            continue
        ids.append(torrent['id'])
    return ids
