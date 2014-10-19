from django.contrib.auth.decorators import login_required
from django.shortcuts import render
import platform
import django
from status.models import StatusEntry, TransInstanceStatus
import subprocess
from WhatManager2.settings import WHAT_USERNAME, DATETIME_FORMAT, FREELEECH_HOSTNAME
from home.models import ReplicaSet, TransInstance, DownloadLocation, get_what_client
import transmissionrpc
import os
import socket


@login_required
def index(request):
    replica_sets = []
    for replica_set in ReplicaSet.objects.all():
        if replica_set.zone not in [u'bibliotik.org', u'what.cd']:
            replica_sets.append(StatusEntry(replica_set.zone, replica_set.name,
                                            u'error', 'Incorrect replica zone'))
        else:
            replica_sets.append(StatusEntry(replica_set.zone, replica_set.name, u'info', None))

    if not replica_sets:
            replica_set.append(StatusEntry('Replica sets', 'Missing',
                                           u'error', 'No ReplicaSet exists. \
                                           Please create at least one'))

    data = {
        "replica_sets": replica_sets
    }
    return render(request, 'status/status.html', data)


@login_required
def check_trans(request):
    transInstances = []
    for instance in TransInstance.objects.all():
        # See if the instance is connectable.
        try:
            instance.client.session_stats()
            transInstances.append(TransInstanceStatus(instance.name, instance.host, instance.port,
                                                      instance.peer_port, instance.username, '',
                                                      u'success', 'Connected'))
        except transmissionrpc.TransmissionError:
            transInstances.append(TransInstanceStatus(instance.name, instance.host, instance.port,
                                                      instance.peer_port, instance.username, '',
                                                      u'error', 'Could not connect to transmission'
                                                      ))

    data = {
        "trans_instances": transInstances,
    }
    return render(request, 'status/trans_status.html', data)


@login_required
def status_environment(request):
    status_entries = []
    status_entries.append(StatusEntry('Locale', subprocess.check_output('locale'), u'info', None))
    if subprocess.call(['git', 'rev-parse', 'HEAD']) == 0:
        status_entries.append(StatusEntry('WhatManager',
                                          (subprocess.check_output(['git', 'rev-parse', 'HEAD'])),
                                          u'info', None))
    else:
        status_entries.append(StatusEntry('WhatManager', 'Not under git revision control. \
                                          Consider cloning git repo', u'info', None))

    status_entries.append(StatusEntry('Python', platform.python_version(), u'info', None))
    status_entries.append(StatusEntry('Django', django.get_version(), u'info', None))

    data = {
        "status_environment": status_entries,
    }
    return render(request, 'status/status_environment.html', data)


@login_required
def status_settings(request):
    settings_entries = [
    ]
    try:
        what_client = get_what_client(request)
        what_client._login()
        settings_entries.append(StatusEntry('What Nickname', WHAT_USERNAME, u'success', ''))
    except Exception:
        settings_entries.append(StatusEntry('What Nickname', WHAT_USERNAME, u'error',
                                            u'Inccorect credentials'))

    settings_entries.append(StatusEntry('DateTime format', DATETIME_FORMAT, u'info', ''))
    if FREELEECH_HOSTNAME != 'NO_EMAILS':
        if FREELEECH_HOSTNAME == socket.gethostname():
            settings_entries.append(StatusEntry('Freeleech hostname', FREELEECH_HOSTNAME,
                                                u'success', 'Hostname correctly set up'))
        else:
            settings_entries.append(StatusEntry('Freeleech hostname', FREELEECH_HOSTNAME,
                                                u'error', 'Freeleech hostname set to %s and \
                                                hostname is %s' %
                                                (FREELEECH_HOSTNAME, socket.gethostname())))

    data = {
        "settings_entries": settings_entries,
    }
    return render(request, 'status/status_settings.html', data)


@login_required
def status_downloadpath(request):
    paths_entry = [
    ]
    locations = DownloadLocation.objects.all()

    if not locations:
        paths_entry.append(StatusEntry('Zone', 'Missing', u'error', 'No download locations set'))
    for location in locations:
        if location.zone not in [u'bibliotik.org', u'what.cd']:
            paths_entry.append(StatusEntry(location.zone, location.path,
                                           u'error', 'Incorrect replica zone'))
        else:
            if os.access(location.path, os.W_OK):
                paths_entry.append(StatusEntry(location.zone, location.path,
                                               u'success', 'Writable'))
            else:
                paths_entry.append(StatusEntry(location.zone, location.path, u'error',
                                               'Location not writable: %s' % location.path))

    data = {
        "download_locations": paths_entry,
    }
    return render(request, 'status/status_downloadlocations.html', data)
