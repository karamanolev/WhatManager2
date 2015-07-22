import base64
import os
import os.path

from django.db import transaction

from WhatManager2.locking import LockModelTables
from WhatManager2.utils import norm_t_torrent
from home.models import ReplicaSet, DownloadLocation, TorrentAlreadyAddedException
from myanonamouse.models import MAMTorrent, MAMTransTorrent


def add_mam_torrent(torrent_id, instance=None, location=None, mam_client=None,
                    add_to_client=True):
    mam_torrent = MAMTorrent.get_or_create(mam_client, torrent_id)

    if not instance:
        instance = ReplicaSet.get_myanonamouse_master().get_preferred_instance()
    if not location:
        location = DownloadLocation.get_myanonamouse_preferred()

    with LockModelTables(MAMTransTorrent):
        try:
            MAMTransTorrent.objects.get(info_hash=mam_torrent.info_hash)
            raise TorrentAlreadyAddedException(u'Already added.')
        except MAMTransTorrent.DoesNotExist:
            pass

        download_dir = os.path.join(location.path, unicode(mam_torrent.id))

        def create_b_torrent():
            new_b_torrent = MAMTransTorrent(
                instance=instance,
                location=location,
                mam_torrent=mam_torrent,
                info_hash=mam_torrent.info_hash,
            )
            new_b_torrent.save()
            return new_b_torrent

        if add_to_client:
            with transaction.atomic():
                b_torrent = create_b_torrent()

                t_torrent = instance.client.add_torrent(
                    base64.b64encode(mam_torrent.torrent_file),
                    download_dir=download_dir,
                    paused=False
                )
                t_torrent = instance.client.get_torrent(
                    t_torrent.id, arguments=MAMTransTorrent.sync_t_arguments)

                if not os.path.exists(download_dir):
                    os.mkdir(download_dir)
                if not os.stat(download_dir).st_mode & 0777 == 0777:
                    os.chmod(download_dir, 0777)

                norm_t_torrent(t_torrent)
                b_torrent.sync_t_torrent(t_torrent)
        else:
            b_torrent = create_b_torrent()
        return b_torrent
