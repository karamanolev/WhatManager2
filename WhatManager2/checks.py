import os

from home.models import ReplicaSet, WhatTorrent, WhatFulltext


def run_checks():
    errors = []
    warnings = []

    # Check WhatFulltext integrity
    def check_whatfulltext():
        w_torrents = dict((w.id, w) for w in WhatTorrent.objects.defer('torrent_file').all())
        w_fulltext = dict((w.id, w) for w in WhatFulltext.objects.all())
        for id, w_t in list(w_torrents.items()):
            if id not in w_fulltext:
                errors.append('{0} does not have a matching fulltext entry.'.format(w_t))
            elif not w_fulltext[id].match(w_t):
                errors.append('{0} does not match info with fulltext entry.'.format(w_t))
        for id, w_f in list(w_fulltext.items()):
            if id not in w_torrents:
                errors.append('{0} does not have a matching whattorrent entry.'.format(w_f))

    check_whatfulltext()

    for replica_set in ReplicaSet.objects.all():
        m_torrents = {}
        for instance in replica_set.transinstance_set.all():
            i_m_torrents = instance.get_m_torrents_by_hash()
            i_t_torrents = instance.get_t_torrents_by_hash(['id', 'hashString'])

            for hash, m_torrent in list(i_m_torrents.items()):
                # Check if this torrent is already in another instance
                if hash in m_torrents:
                    warnings.append('{0} is already in another instance of '
                                    'the same replica set: {1}'
                                    .format(m_torrent, m_torrents[hash].instance))
                # Check if the instance has the torrent
                if hash not in i_t_torrents:
                    errors.append('{0} is in DB, but not in Transmission at instance {1}'
                                  .format(m_torrent, instance))

                m_torrents[hash] = m_torrent

                # Check for the presence of metafiles if the instance is a master
                if replica_set.is_master:
                    files_in_dir = os.listdir(m_torrent.path)
                    if not any('.torrent' in f for f in files_in_dir):
                        errors.append('Missing .torrent file for {0} at {1}'
                                      .format(m_torrent, instance))
                    if not any('ReleaseInfo2.txt' == f for f in files_in_dir):
                        errors.append('Missing ReleaseInfo2.txt for {0} at {1}'
                                      .format(m_torrent, instance))

            for hash, t_torrent in list(i_t_torrents.items()):
                # Check if the database has the torrent
                if hash not in i_m_torrents:
                    errors.append('{0} is in Transmission, but not in DB at instance {1}'
                                  .format(t_torrent, instance))

    return {
        'errors': errors,
        'warnings': warnings
    }
