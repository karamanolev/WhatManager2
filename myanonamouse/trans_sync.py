import os
import os.path

from django.db import transaction

from home.models import LogEntry, DownloadLocation
from myanonamouse import manage_mam
from myanonamouse.models import MAMTransTorrent, MAMTorrent


def sync_instance_db(instance):
    mam_torrents = instance.get_mam_torrents_by_hash()
    t_torrents = instance.get_t_torrents_by_hash(MAMTransTorrent.sync_t_arguments)

    for c_hash, mam_torrent in list(mam_torrents.items()):
        if c_hash not in t_torrents:
            mam_torrent_path = mam_torrent.path.encode('utf-8')

            messages = []
            with transaction.atomic():
                mam_torrent.delete()
                del mam_torrents[c_hash]

                if instance.replica_set.is_master:
                    if os.path.exists(mam_torrent_path):
                        files = os.listdir(mam_torrent_path)
                        if len(files):
                            messages.append('There are other files so leaving in place.')
                        else:
                            messages.append('No other files. Deleting directory.')
                            os.rmdir(mam_torrent_path)
                    else:
                        messages.append('Path does not exist.')

            LogEntry.add(None, 'action',
                         'MAM torrent {0} deleted from instance {1}. {2}'
                         .format(mam_torrent, instance, ' '.join(messages)))

    with transaction.atomic():
        for c_hash, t_torrent in list(t_torrents.items()):
            if c_hash not in mam_torrents:
                torrent_id = int(os.path.basename(t_torrent.downloadDir))
                w_torrent = MAMTorrent.get_or_create(None, torrent_id)
                d_location = DownloadLocation.get_by_full_path(t_torrent.downloadDir)
                m_torrent = manage_mam.add_mam_torrent(w_torrent.id, instance,
                                                       d_location, None, False)
                mam_torrents[m_torrent.info_hash] = m_torrent
                LogEntry.add(None, 'action',
                             'MAM torrent {0} appeared in instance {1}.'
                             .format(t_torrent.name, instance))
            else:
                mam_torrent = mam_torrents[c_hash]
                mam_torrent.sync_t_torrent(t_torrent)


def sync_all_instances_db(replica_set):
    for instance in replica_set.transinstance_set.all():
        sync_instance_db(instance)


def init_sync_instance_db(instance):
    mam_torrents = instance.get_mam_torrents_by_hash()
    t_torrents = instance.get_t_torrents_by_hash(MAMTransTorrent.sync_t_arguments)

    with transaction.atomic():
        for c_hash, t_torrent in list(t_torrents.items()):
            if c_hash not in mam_torrents:
                try:
                    mam_torrent = MAMTorrent.objects.get(info_hash=c_hash)
                    d_location = DownloadLocation.get_by_full_path(t_torrent.downloadDir)

                    mam_torrent = manage_mam.add_mam_torrent(
                        mam_torrent.id,
                        instance,
                        d_location,
                        add_to_client=False
                    )
                    mam_torrents[mam_torrent.info_hash] = mam_torrent
                except MAMTorrent.DoesNotExist:
                    raise Exception('Could not find hash {0} for name {1} in '
                                    'DB during initial sync.'
                                    .format(c_hash, t_torrent.name))

            mam_torrent = mam_torrents[c_hash]
            mam_torrent.sync_t_torrent(t_torrent)


def init_sync_all_instances_db(replica_set):
    for instance in replica_set.transinstance_set.all():
        init_sync_instance_db(instance)
