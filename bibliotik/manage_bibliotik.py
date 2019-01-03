import base64
import os
import os.path

from django.db import transaction

from WhatManager2.locking import LockModelTables
from WhatManager2.utils import norm_t_torrent
from bibliotik.models import BibliotikTorrent, BibliotikTransTorrent
from home.models import ReplicaSet, DownloadLocation, TorrentAlreadyAddedException, TransInstance


def add_bibliotik_torrent(torrent_id, instance=None, location=None, bibliotik_client=None,
                          add_to_client=True):
    bibliotik_torrent = BibliotikTorrent.get_or_create(bibliotik_client, torrent_id)

    if not instance:
        instance = ReplicaSet.get_bibliotik_master().get_preferred_instance()
    if not location:
        location = DownloadLocation.get_bibliotik_preferred()

    with LockModelTables(BibliotikTransTorrent, TransInstance):
        try:
            existing_one = BibliotikTransTorrent.objects.get(info_hash=bibliotik_torrent.info_hash)
            raise TorrentAlreadyAddedException('Already added (instance={0}, new_instance={1}, info_hash={2}).'.format(
                 instance, existing_one.instance, bibliotik_torrent.info_hash))
        except BibliotikTransTorrent.DoesNotExist:
            pass

        download_dir = os.path.join(location.path, str(bibliotik_torrent.id))

        def create_b_torrent():
            new_b_torrent = BibliotikTransTorrent(
                instance=instance,
                location=location,
                bibliotik_torrent=bibliotik_torrent,
                info_hash=bibliotik_torrent.info_hash,
            )
            new_b_torrent.save()
            return new_b_torrent

        if add_to_client:
            with transaction.atomic():
                b_torrent = create_b_torrent()

                t_torrent = instance.client.add_torrent(
                    base64.b64encode(bibliotik_torrent.torrent_file),
                    download_dir=download_dir,
                    paused=False
                )
                t_torrent = instance.client.get_torrent(
                    t_torrent.id, arguments=BibliotikTransTorrent.sync_t_arguments)

                if not os.path.exists(download_dir):
                    os.mkdir(download_dir)
                if not os.stat(download_dir).st_mode & 0o777 == 0o777:
                    os.chmod(download_dir, 0o777)

                norm_t_torrent(t_torrent)
                b_torrent.sync_t_torrent(t_torrent)
        else:
            b_torrent = create_b_torrent()
        return b_torrent
