import os
import shutil

from django.db import transaction
from django.utils import timezone

from WhatManager2 import manage_torrent, settings
from WhatManager2.settings import SYNC_SYNCS_FILES
from home.models import WhatTorrent, DownloadLocation, TransTorrent, LogEntry, ReplicaSet, \
    WhatFulltext, get_what_client
from what_profile.models import WhatUserSnapshot


def sync_fulltext():
    fixed = False
    w_torrents = dict((w.id, w) for w in WhatTorrent.objects.all())
    w_fulltext = dict((w.id, w) for w in WhatFulltext.objects.all())
    for id, w_t in list(w_torrents.items()):
        if id not in w_fulltext:
            WhatFulltext(id=w_t.id, info=w_t.info).save()
            fixed = True
        elif not w_fulltext[id].match(w_t):
            w_fulltext[id].update(w_t)
            fixed = True
    for id, w_f in list(w_fulltext.items()):
        if id not in w_torrents:
            w_f.delete()
            fixed = True
    return fixed


def sync_instance_db(request, instance):
    m_torrents = instance.get_m_torrents_by_hash()
    t_torrents = instance.get_t_torrents_by_hash(TransTorrent.sync_t_arguments)

    for hash, m_torrent in list(m_torrents.items()):
        if hash not in t_torrents:
            m_torrent_path = m_torrent.path.encode('utf-8')

            messages = []
            with transaction.atomic():
                m_torrent.delete()
                del m_torrents[hash]

                if instance.replica_set.is_master:
                    if os.path.exists(m_torrent_path):
                        files = os.listdir(m_torrent_path)
                        if any(f for f in files if '.torrent' not in f and 'ReleaseInfo2.txt' != f):
                            messages.append('There are other files so leaving in place.')
                        else:
                            messages.append('No other files. Deleting directory.')
                            shutil.rmtree(m_torrent_path)
                    else:
                        messages.append('Path does not exist.')

            LogEntry.add(None, 'action', 'Torrent {0} deleted from instance {1}. {2}'
                         .format(m_torrent, instance, ' '.join(messages)))

    with transaction.atomic():
        for hash, t_torrent in list(t_torrents.items()):
            if hash not in m_torrents:
                w_torrent = WhatTorrent.get_or_create(request, info_hash=hash)
                d_location = DownloadLocation.get_by_full_path(t_torrent.downloadDir)
                m_torrent = manage_torrent.add_torrent(request, instance, d_location, w_torrent.id,
                                                       False)
                m_torrents[m_torrent.info_hash] = m_torrent
                LogEntry.add(None, 'action', 'Torrent {0} appeared in instance {1}. Added to DB.'
                             .format(m_torrent, instance))

            m_torrent = m_torrents[hash]
            m_torrent.sync_t_torrent(t_torrent)
            if (SYNC_SYNCS_FILES or 'sync_files' in request.GET) and instance.replica_set.is_master:
                m_torrent.sync_files()


def sync_all_instances_db(request, replica_set):
    for instance in replica_set.transinstance_set.all():
        sync_instance_db(request, instance)


def sync_replica_set(master, slave):
    master_m_torrents = {}
    slave_m_torrents = {}

    for master_instance in master.transinstance_set.all():
        for hash, m_torrent in list(master_instance.get_m_torrents_by_hash().items()):
            if m_torrent.torrent_done == 1:
                master_m_torrents[hash] = m_torrent
    for slave_instance in slave.transinstance_set.all():
        slave_m_torrents.update(slave_instance.get_m_torrents_by_hash())

    for hash, m_torrent in list(master_m_torrents.items()):
        if hash not in slave_m_torrents:
            instance = slave.get_preferred_instance()
            manage_torrent.add_torrent(None, instance, m_torrent.location,
                                       m_torrent.what_torrent_id, True)
            LogEntry.add(None, 'info', 'Torrent {0} added to {1} during replication.'
                         .format(m_torrent, instance))
    for hash, m_torrent in list(slave_m_torrents.items()):
        if hash not in master_m_torrents:
            manage_torrent.remove_torrent(m_torrent)
            LogEntry.add(None, 'info', 'Torrent {0} removed from {1} during replication'
                         .format(m_torrent, m_torrent.instance))


def sync_all_replicas_to_master():
    for replica_set in ReplicaSet.objects.filter(zone=ReplicaSet.ZONE_WHAT):
        if not replica_set.is_master:
            sync_replica_set(ReplicaSet.get_what_master(), replica_set)


def sync_profile(request):
    user_id = settings.WHAT_USER_ID
    interval = settings.WHAT_PROFILE_SNAPSHOT_INTERVAL
    try:
        last_snap = WhatUserSnapshot.get_last()
        if (timezone.now() - last_snap.datetime).total_seconds() < interval - 30:
            return
    except WhatUserSnapshot.DoesNotExist:
        pass
    what = get_what_client(request)
    WhatUserSnapshot.get(what, user_id).save()
