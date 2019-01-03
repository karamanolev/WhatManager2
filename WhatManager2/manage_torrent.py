import os

from django.db import transaction

from WhatManager2.locking import LockModelTables
from WhatManager2.utils import norm_t_torrent, dummy_context_manager
from home.models import WhatTorrent, TransTorrent, TorrentAlreadyAddedException, LogEntry, \
    ReplicaSet


def add_torrent(request, instance, download_location, what_id, add_to_client=True, moving=False):
    w_torrent = WhatTorrent.get_or_create(request, what_id=what_id)

    masters = list(ReplicaSet.get_what_master().transinstance_set.all())
    with LockModelTables(TransTorrent, LogEntry):
        if add_to_client and not moving:
            try:
                existing_one = TransTorrent.objects.get(instance__in=masters, info_hash=w_torrent.info_hash)
                raise TorrentAlreadyAddedException('Already added (instance={0}, new_instance={1}, info_hash={2}).'.format(
                    instance, existing_one.instance, w_torrent.info_hash))
            except TransTorrent.DoesNotExist:
                pass

        if add_to_client:
            manager = transaction.atomic
        else:
            manager = dummy_context_manager

        with manager():
            if True:
                m_torrent = TransTorrent(
                    instance=instance,
                    location=download_location,
                    what_torrent=w_torrent,
                    info_hash=w_torrent.info_hash,
                )
                m_torrent.save()

                if add_to_client:
                    download_dir = os.path.join(download_location.path, str(w_torrent.id))
                    t_torrent = instance.client.add_torrent(
                        w_torrent.torrent_file,
                        download_dir=download_dir,
                        paused=False
                    )
                    t_torrent = instance.client.get_torrent(t_torrent.id,
                                                            arguments=TransTorrent.sync_t_arguments)
                    norm_t_torrent(t_torrent)
                    m_torrent.sync_t_torrent(t_torrent)
                    m_torrent.sync_files()
                return m_torrent


def remove_torrent(m_torrent):
    with transaction.atomic():
        m_torrent.instance.client.remove_torrent(m_torrent.torrent_id, False)
        m_torrent.delete()


def move_torrent(m_torrent, new_instance):
    with transaction.atomic():
        new_m_torrent = add_torrent(None, new_instance, m_torrent.location,
                                    m_torrent.what_torrent.id, True, True)
        remove_torrent(m_torrent)
    return new_m_torrent
