import os
import os.path

from django.db import transaction

from bibliotik import manage_bibliotik
from bibliotik.models import BibliotikTransTorrent, BibliotikTorrent
from home.models import LogEntry, DownloadLocation


def sync_instance_db(instance):
    b_torrents = instance.get_b_torrents_by_hash()
    t_torrents = instance.get_t_torrents_by_hash(BibliotikTransTorrent.sync_t_arguments)

    for c_hash, b_torrent in list(b_torrents.items()):
        if c_hash not in t_torrents:
            b_torrent_path = b_torrent.path.encode('utf-8')

            messages = []
            with transaction.atomic():
                b_torrent.delete()
                del b_torrents[c_hash]

                if instance.replica_set.is_master:
                    if os.path.exists(b_torrent_path):
                        files = os.listdir(b_torrent_path)
                        if len(files):
                            messages.append('There are other files so leaving in place.')
                        else:
                            messages.append('No other files. Deleting directory.')
                            os.rmdir(b_torrent_path)
                    else:
                        messages.append('Path does not exist.')

            LogEntry.add(None, 'action',
                         'Bibliotik torrent {0} deleted from instance {1}. {2}'
                         .format(b_torrent, instance, ' '.join(messages)))

    with transaction.atomic():
        for c_hash, t_torrent in list(t_torrents.items()):
            if c_hash not in b_torrents:
                torrent_id = int(os.path.basename(t_torrent.downloadDir))
                w_torrent = BibliotikTorrent.get_or_create(None, torrent_id)
                d_location = DownloadLocation.get_by_full_path(t_torrent.downloadDir)
                m_torrent = manage_bibliotik.add_bibliotik_torrent(w_torrent.id, instance,
                                                                   d_location, None, False)
                b_torrents[m_torrent.info_hash] = m_torrent
                LogEntry.add(None, 'action',
                             'Bibliotik torrent {0} appeared in instance {1}.'
                             .format(t_torrent.name, instance))
            else:
                b_torrent = b_torrents[c_hash]
                b_torrent.sync_t_torrent(t_torrent)


def sync_all_instances_db(replica_set):
    for instance in replica_set.transinstance_set.all():
        sync_instance_db(instance)


def init_sync_instance_db(instance):
    b_torrents = instance.get_b_torrents_by_hash()
    t_torrents = instance.get_t_torrents_by_hash(BibliotikTransTorrent.sync_t_arguments)

    with transaction.atomic():
        for c_hash, t_torrent in list(t_torrents.items()):
            if c_hash not in b_torrents:
                try:
                    bibliotik_torrent = BibliotikTorrent.objects.get(info_hash=c_hash)
                    d_location = DownloadLocation.get_by_full_path(t_torrent.downloadDir)

                    b_torrent = manage_bibliotik.add_bibliotik_torrent(
                        bibliotik_torrent.id,
                        instance,
                        d_location,
                        add_to_client=False
                    )
                    b_torrents[b_torrent.info_hash] = b_torrent
                except BibliotikTorrent.DoesNotExist:
                    raise Exception('Could not find hash {0} for name {1} in '
                                    'DB during initial sync.'
                                    .format(c_hash, t_torrent.name))

            b_torrent = b_torrents[c_hash]
            b_torrent.sync_t_torrent(t_torrent)


def init_sync_all_instances_db(replica_set):
    for instance in replica_set.transinstance_set.all():
        init_sync_instance_db(instance)
