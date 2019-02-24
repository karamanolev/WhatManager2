#!/usr/bin/env python

from __future__ import unicode_literals

import requests
import time
from django.core.management.base import BaseCommand

from WhatManager2.utils import wm_unicode
from home.models import get_what_client
from what_transcode.tasks import TranscodeSingleJob


def _add_to_wm_transcode(what_id):
    print 'Adding {0} to wm'.format(what_id)
    post_data = {
        'what_id': what_id,
    }
    response = requests.post('https://karamanolev.com/wm/transcode/request', data=post_data,
                             auth=('', ''))
    response_json = response.json()
    if response_json['message'] != 'Request added.':
        raise Exception('Cannot add {0} to wm: {1}'.format(what_id, response_json['message']))


def add_to_wm_transcode(what_id):
    for i in range(2):
        try:
            _add_to_wm_transcode(what_id)
            return
        except Exception:
            print 'Error adding to wm, trying again in 2 sec...'
            time.sleep(3)
    _add_to_wm_transcode(what_id)


def report_progress(msg):
    print msg


class Command(BaseCommand):
    help = 'Help you create a torrent and add it to WM'

    def add_arguments(self, parser):
        parser.add_argument('source_dir', required=True, help='Source directory for the torrent.')

    def handle(self, *args, **options):
        source_dir = wm_unicode(options['source_dir'])
        if not source_dir:
            print u'Pass only the source directory.'
            return 1

        if source_dir.endswith('/'):
            source_dir = source_dir[:-1]

        what = get_what_client(lambda: None)
        job = TranscodeSingleJob(what, None, report_progress, None, None, source_dir)
        job.create_torrent()
        raw_input('Please upload the torrent and press enter...')
        job.move_torrent_to_dest()
        add_to_wm_transcode(job.new_torrent['torrent']['id'])
