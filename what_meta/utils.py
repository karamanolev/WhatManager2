from django.core.urlresolvers import reverse
from django.utils.http import urlquote

from WhatManager2.utils import get_artists_list, get_artists, html_unescape

from home import info_holder
from home.models import WhatTorrent, TransTorrent, ReplicaSet
from player.player_utils import get_metadata_dict, get_playlist_files
from what_meta.filtering import sort_filter_torrents
from whatify.utils import extended_artists_to_music_info


def get_image_cache_url(url):
    if url is None:
        return None
    resolved_url = reverse('what_meta.views.image', args=['url_placeholder'])
    return resolved_url.replace('url_placeholder', urlquote(url, ''))


def get_artist_alias_dict(artist_alias, *args, **kwargs):
    data = get_artist_dict(artist_alias.artist, *args, **kwargs)
    data['name'] = artist_alias.name
    return data


def get_artist_dict(artist, include_all=False):
    data = {
        'id': artist.id,
        'name': artist.name,
        'image': get_image_cache_url(artist.image),
        'wiki': artist.wiki_body,
    }
    if include_all:
        assert not artist.is_shell, 'Can not get torrents for a shell artist'
        data['tags'] = sorted(artist.info['tags'], key=lambda tag: tag['count'], reverse=True)
        torrent_groups_by_id = {t['groupId']: t for t in artist.info['torrentgroup']}
        torrent_groups = list(torrent_groups_by_id.values())
        group_ids = list(torrent_groups_by_id.keys())
        torrent_ids = WhatTorrent.objects.filter(
            torrent_group_id__in=group_ids).values_list('id', flat=True)
        torrents_done = {
            t.what_torrent_id: t.torrent_done for t in
            TransTorrent.objects.filter(what_torrent_id__in=torrent_ids)
        }

        data.update({
            'torrent_groups': {
                releaseTypeName: [
                    get_artist_group_dict(torrents_done, t)
                    for t in sorted(torrent_groups, key=lambda g: g['groupYear'], reverse=True)
                    if t['releaseType'] == releaseTypeId
                ]
                for releaseTypeId, releaseTypeName in info_holder.WHAT_RELEASE_TYPES
            } if not artist.is_shell else None,
        })
    return data


def get_artist_group_dict(torrents_done, torrent_group):
    have = False
    for torrent in sort_filter_torrents(torrent_group['torrent']):
        if torrent['id'] in torrents_done:
            done = torrents_done[torrent['id']]
            if done == 1:
                have = True
            elif have is not True:
                have = max(have, done)
    music_info = extended_artists_to_music_info(torrent_group['extendedArtists'])
    return {
        'id': torrent_group['groupId'],
        'joined_artists': get_artists(music_info),
        'artists': get_artists_list(music_info),
        'name': html_unescape(torrent_group['groupName']),
        'year': torrent_group['groupYear'],
        'wiki_image': get_image_cache_url(torrent_group['wikiImage']),
        'have': have,
    }


def get_torrent_group_dict(torrent_group):
    return {
        'id': torrent_group.id,
        'joined_artists': torrent_group.joined_artists,
        'artists': get_artists_list(torrent_group.info),
        'name': torrent_group.name,
        'year': torrent_group.year,
        'wiki_image': get_image_cache_url(torrent_group.wiki_image),
        'wiki_body': torrent_group.wiki_body,
    }


def get_torrent_group_playlist_or_have(torrent_group):
    torrents = sort_filter_torrents(torrent_group.whattorrent_set.all())
    masters = ReplicaSet.get_what_master().transinstance_set.all()
    trans_torrents = {
        t.what_torrent_id: t for t in
        TransTorrent.objects.filter(what_torrent__in=torrents, instance__in=masters)
    }
    torrent = None
    for candidate in torrents:
        trans_torrent = trans_torrents[candidate.id]
        if trans_torrent is not None and trans_torrent.torrent_done == 1:
            torrent = candidate
            break
    if torrent is None:
        for candidate in torrents:
            trans_torrent = trans_torrents[candidate.id]
            done = trans_torrent.torrent_done
            if torrent is None or done > trans_torrents[torrent.id].torrent_done:
                torrent = candidate
    if torrent:
        trans_torrent = trans_torrents[torrent.id]
        if trans_torrent.torrent_done == 1:
            return {
                'playlist': [
                    {
                        'id': 'what/' + str(torrent.id) + '#' + str(i),
                        'url': reverse('player.views.get_file') + '?path=' + urlquote(path, ''),
                        'metadata': get_metadata_dict(path)
                    }
                    for i, path in enumerate(get_playlist_files('what/' + str(torrent.id))[1])
                ]
            }
        else:
            return {
                'have': trans_torrent.torrent_done
            }
    return dict()
