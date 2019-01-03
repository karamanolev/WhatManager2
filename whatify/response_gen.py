from collections import defaultdict

from django.urls import reverse
from django.utils.http import urlquote

from WhatManager2.utils import get_artists, get_artists_list
from home.info_holder import WHAT_RELEASE_TYPES
from home.models import WhatTorrent, TransTorrent, ReplicaSet, WhatFileMetadataCache
from what_transcode.utils import html_unescape
from whatify.filtering import sort_filter_torrents
from whatify.utils import extended_artists_to_music_info


def get_image_cache_url(url):
    if url is None:
        return None
    return reverse('what_meta.views.image') + '?url=' + urlquote(url, '')


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
        torrent_groups = {t['groupId']: t for t in artist.info['torrentgroup']}
        torrent_groups_have = get_torrent_groups_have(list(torrent_groups.keys()), True)
        torrent_groups = list(torrent_groups.values())
        torrent_groups.sort(key=lambda g: g['groupYear'], reverse=True)

        main_artist_groups = defaultdict(list)
        for torrent_group in torrent_groups:
            if torrent_group['artists'] is None:
                continue
            if any(artist.id == a['id'] for a in torrent_group['artists']):
                item_data = get_artist_group_dict(torrent_group)
                item_data.update(torrent_groups_have[torrent_group['groupId']])
                main_artist_groups[torrent_group['releaseType']].append(item_data)
        categories = []
        for release_type in WHAT_RELEASE_TYPES:
            if main_artist_groups[release_type[0]]:
                categories.append({
                    'name': release_type[1],
                    'torrent_groups': main_artist_groups[release_type[0]],
                })
        data['categories'] = categories
        data['tags'] = sorted(artist.info['tags'], key=lambda tag: tag['count'], reverse=True)
    return data


def get_artist_group_dict(torrent_group):
    music_info = extended_artists_to_music_info(torrent_group['extendedArtists'])
    return {
        'id': torrent_group['groupId'],
        'joined_artists': get_artists(music_info),
        'artists': get_artists_list(music_info),
        'name': html_unescape(torrent_group['groupName']),
        'year': torrent_group['groupYear'],
        'wiki_image': get_image_cache_url(torrent_group['wikiImage']),
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


def get_torrent_groups_have(torrent_group_ids, sync_torrents=False):
    torrent_group_ids = list(torrent_group_ids)
    masters = ReplicaSet.get_what_master().transinstance_set.all()
    what_torrents = {
        w_t.id: w_t for w_t in
        WhatTorrent.objects.filter(torrent_group_id__in=torrent_group_ids)
    }
    trans_torrents = TransTorrent.objects.filter(
        what_torrent__in=what_torrents, instance__in=masters).prefetch_related('location')
    trans_torrents_by_group = defaultdict(list)
    for t_t in trans_torrents:
        w_t = what_torrents[t_t.what_torrent_id]
        trans_torrents_by_group[w_t.torrent_group_id].append((w_t, t_t))
    return {
        torrent_group_id: get_torrent_group_have(
            trans_torrents_by_group[torrent_group_id], sync_torrents) for
        torrent_group_id in torrent_group_ids
    }


def get_torrent_group_have(what_trans_torrents, sync_torrents=False):
    what_torrents = [w_t[0] for w_t in what_trans_torrents]
    trans_torrents = {w_t[0].id: w_t[1] for w_t in what_trans_torrents}

    torrents = sort_filter_torrents(what_torrents)
    torrent = None
    for candidate in torrents:
        trans_torrent = trans_torrents.get(candidate.id)
        if trans_torrent is None:
            continue
        if trans_torrent.torrent_done == 1:
            torrent = candidate
            break
    if torrent is None:
        for candidate in torrents:
            trans_torrent = trans_torrents.get(candidate.id)
            if trans_torrent is None:
                continue
            if sync_torrents:
                trans_torrent.sync_t_torrent()
            done = trans_torrent.torrent_done
            if torrent is None or done > trans_torrents[torrent.id].torrent_done:
                torrent = candidate
    if torrent:
        trans_torrent = trans_torrents[torrent.id]
        if trans_torrent.torrent_done == 1:
            cache_entries = WhatFileMetadataCache.get_metadata_batch(torrent, trans_torrent, False)
            duration = sum(c.duration for c in cache_entries)
            return {
                'have': True,
                'duration': duration,
                'playlist': [
                    {
                        'id': 'what/' + str(torrent.id) + '#' + str(i),
                        'url': reverse('player.views.get_file') + '?path=' + urlquote(
                            entry.path, ''),
                        'metadata': entry.easy
                    }
                    for i, entry in enumerate(cache_entries)
                ],
            }
        else:
            return {
                'have': trans_torrent.torrent_done
            }
    return {
        'have': False
    }
