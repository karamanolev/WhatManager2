#!/usr/bin/env python
import base64
import time
import os
import subprocess
import os.path
import json

from django.core.management.base import BaseCommand
import requests

from WhatManager2.settings import FILES_SYNC_HTTP_USERNAME, FILES_SYNC_HTTP_PASSWORD, \
    FILES_SYNC_SSH, FILES_SYNC_WM_ROOT
from WhatManager2.utils import read_text
from home.models import DownloadLocation, ReplicaSet, TransTorrentBase


wm_auth = (FILES_SYNC_HTTP_USERNAME, FILES_SYNC_HTTP_PASSWORD)


def call_rsync(path):
    if not path.endswith('/'):
        path += '/'
    subprocess.call(['rsync', '-rtzpP', '--delete',
                     FILES_SYNC_SSH + ':' + path,
                     path])


def get_torrent(torrent_id):
    return requests.get('{0}/books/bibliotik/json/get_torrent_file/{1}'.format(
        FILES_SYNC_WM_ROOT, torrent_id), params={'auth': 'http'}, auth=wm_auth).content


def torrents_status(torrent_ids):
    return json.loads(
        requests.get('{0}/books/bibliotik/json/torrents_info'.format(FILES_SYNC_WM_ROOT), params={
            'ids': ','.join(torrent_ids),
            'auth': 'http'
        }, auth=wm_auth).text)


def monitor_torrent(client, t_id):
    print('Monitoring transmission_id={0}'.format(t_id))
    while True:
        t_torrent = client.get_torrent(t_id, arguments=['id', 'status'])
        if t_torrent.status in ['seed pending', 'seeding']:
            print('Torrent {0} is {1}. OK.'.format(t_id, t_torrent.status))
            break
        elif t_torrent.status in ['download pending', 'downloading']:
            print('Torrent {0} is {1}. Stopping it!!!'.format(t_id, t_torrent.status))
            client.stop_torrent(t_id)
            break
        elif t_torrent.status in ['check pending', 'checking']:
            print('Torrent {0} is {1}. Waiting more...'.format(t_id, t_torrent.status))
        elif t_torrent.status in ['stopped']:
            print('Torrent {0} is {1}. Whatever...'.format(t_id, t_torrent.status))
            break
        time.sleep(0.5)


def chunks(l, n):
    c_buffer = list()
    for item in l:
        c_buffer.append(item)
        if len(c_buffer) >= n:
            yield c_buffer
            c_buffer = list()
    if len(c_buffer):
        yield c_buffer


def check_running():
    pids = [pid for pid in os.listdir('/proc') if pid.isdigit()]

    found_cmdlines = list()
    for pid in pids:
        cmdline = read_text(os.path.join('/proc', pid, 'cmdline')).split('\0')
        if 'python' in cmdline[0] and 'transmission_files_sync' in cmdline:
            found_cmdlines.append(' '.join(cmdline))
    if len(found_cmdlines) != 1:
        raise Exception('Script is probably already running or error checking. Found {0}.'.format(
            '; '.join(found_cmdlines)))


class Command(BaseCommand):
    help = 'Provisions transmission instances'

    def handle(self, *args, **options):
        try:
            self.download_locations = list(DownloadLocation.objects.filter(
                zone=ReplicaSet.ZONE_BIBLIOTIK))
            self.files_sync()
        except Exception as ex:
            with open('/files_sync_error.txt', 'w') as f:
                f.write(str(ex))
                f.write('\n')

    def call_rsyncs(self):
        for dl in self.download_locations:
            call_rsync(dl.path)

    def files_sync(self):
        check_running()

        print('Running initial rsync...')
        self.call_rsyncs()

        print('Iterating instances...')
        current_torrents = {}
        best_instance = None
        for instance in ReplicaSet.get_bibliotik_master().transinstance_set.all():
            t_torrents = instance.get_t_torrents(TransTorrentBase.sync_t_arguments)
            if best_instance is None or len(t_torrents) < best_instance[0]:
                best_instance = (len(t_torrents), instance)
            for t_torrent in t_torrents:
                part = t_torrent.downloadDir.rpartition('/')
                current_torrents[int(part[2])] = {
                    'download_dir': part[0],
                }

        new_torrents = {}
        print('Iterating locations...')
        for location in DownloadLocation.objects.filter(zone=ReplicaSet.ZONE_BIBLIOTIK):
            for i in os.listdir(location.path):
                torrent_id = int(i)
                if torrent_id not in current_torrents:
                    new_torrents[torrent_id] = {
                        'id': torrent_id,
                        'location': location,
                    }
                else:
                    del current_torrents[torrent_id]

        to_add = list()
        for batch_number, batch in enumerate(chunks(iter(new_torrents.values()), 100)):
            print('Requests status for batch {0}...'.format(batch_number))
            batch_status = torrents_status(str(i['id']) for i in batch)
            for row in batch_status:
                if row['status'] == 'downloaded':
                    to_add.append(new_torrents[row['id']])

        print('Running second rsync...')
        self.call_rsyncs()

        preferred_instance = best_instance[1]
        for row in to_add:
            print('Downloading torrent {0}'.format(row['id']))
            torrent_file = get_torrent(row['id'])
            print('Adding torrent {0}'.format(row['id']))
            t_torrent = preferred_instance.client.add_torrent(
                base64.b64encode(torrent_file),
                download_dir=os.path.join(str(row['location'].path), str(row['id'])),
                paused=False
            )
            monitor_torrent(preferred_instance.client, t_torrent.id)

        print('Completed.')
