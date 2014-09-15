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
