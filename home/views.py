from collections import defaultdict
import os

from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import render

from WhatManager2.utils import json_return_method
from home.models import ReplicaSet, DownloadLocation


@login_required
def dashboard(request):
    data = {
    }
    return render(request, 'home/dashboard.html', data)


@login_required
def torrents(request):
    data = {
    }
    return render(request, 'home/torrents.html', data)


@login_required
def view_log(request):
    data = {
    }
    return render(request, 'home/view_log.html', data)


@login_required
def checks(request):
    return render(request, 'home/checks.html')


@login_required
def stats(request):
    return render(request, 'home/stats.html')


@login_required
@user_passes_test(lambda u: u.is_superuser is True)
@json_return_method
def add_all(request):
    what_ids = set()
    for instance in ReplicaSet.get_what_master().transinstance_set.all():
        for m_torrent in instance.transtorrent_set.all():
            if m_torrent.what_torrent_id in what_ids:
                raise Exception('Duplcate what_id in transmission')
            what_ids.add(m_torrent.what_torrent_id)
    dest_dir = request.GET['path']
    if dest_dir not in [p.path for p in DownloadLocation.objects.filter(zone=ReplicaSet.ZONE_WHAT)]:
        raise Exception('Path not allowed')
    dest_dir_ids = {int(i) for i in os.listdir(dest_dir)}
    return {
        'torrents in dir': len(dest_dir_ids),
        'torrents in transmissions': len(what_ids),
        'torrents not added': list(dest_dir_ids - what_ids),
        'torrents missing': list(what_ids - dest_dir_ids)
    }


@login_required
@user_passes_test(lambda u: u.is_superuser is True)
@json_return_method
def remove_transmission_dupes(request):
    dupes = defaultdict(list)
    for instance in ReplicaSet.get_what_master().transinstance_set.all():
        for m_torrent in instance.transtorrent_set.all():
            dupes[m_torrent.what_torrent_id].append(instance.name + '/' + str(m_torrent.torrent_id))
            if len(dupes[m_torrent.what_torrent_id]) > 1:
                if 'remove' in request.GET:
                    instance.client.remove_torrent(m_torrent.torrent_id)
    return list(i for i in dupes.items() if len(i[1]) > 1)


@login_required
def userscripts(request):
    return render(request, 'home/userscripts.html')
