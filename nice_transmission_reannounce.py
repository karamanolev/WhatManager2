#!/usr/bin/env python
import os
import sys
import time

os.environ['DJANGO_SETTINGS_MODULE'] = 'WhatManager2.settings'

from home.models import ReplicaSet

BATCH_SIZE = 50

master = ReplicaSet.get_what_master()
instances = master.transinstance_set.all()


def is_torrent_errored(torrent):
    if torrent.error:
        return True
    for tracker in torrent.trackerStats:
        if not tracker['lastAnnounceSucceeded']:
            return True
    return False


def run_reannounce(sleep_time):
    for instance in instances:
        print instance
        client = instance.client
        torrents = client.get_torrents(arguments=['id', 'name', 'error', 'errorString', 'status', 'trackerStats'])
        error_torrents = [t for t in torrents if is_torrent_errored(t)]
        batch_start = 0
        while batch_start < len(error_torrents):
            batch = error_torrents[batch_start:batch_start + BATCH_SIZE]
            print 'Processing batch from', batch_start, 'to', batch_start + len(batch), '/', len(error_torrents)
            batch_start += len(batch)
            client.reannounce_torrent([t.id for t in batch])
            time.sleep(sleep_time)


if __name__ == '__main__':
    sleep_time = 2
    if '--fast' in sys.argv:
        sleep_time = 0.5
    run_reannounce(sleep_time) 
