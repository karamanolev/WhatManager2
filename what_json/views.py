import json
import os
from random import choice
import shutil
import socket
import traceback
import time

from django.contrib.auth.decorators import login_required, user_passes_test, permission_required
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

import WhatManager2.checks
from WhatManager2 import manage_torrent, trans_sync
from WhatManager2.settings import MIN_FREE_DISK_SPACE, FREELEECH_EMAIL_THRESHOLD, FREELEECH_HOSTNAME
from WhatManager2.templatetags.custom_filters import filesizeformat
from WhatManager2.utils import json_return_method
from home.models import ReplicaSet, LogEntry, TransTorrent, TorrentAlreadyAddedException, WhatTorrent, DownloadLocation, \
    TransInstance, get_what_client, send_freeleech_email, \
    RequestException


@login_required
@user_passes_test(lambda u: u.is_superuser is True)
@json_return_method
def sync(request):
    start_time = time.time()
    part_start_time = time.time()
    try:
        trans_sync.sync_profile(request)
        profile_time = time.time() - part_start_time
        part_start_time = time.time()
    except Exception as ex:
        tb = traceback.format_exc()
        LogEntry.add(request.user, u'error', u'Error syncing profile: {0}'.format(ex), tb)

    try:
        master = ReplicaSet.get_what_master()
        trans_sync.sync_all_instances_db(request, master)
        master_db_time = time.time() - part_start_time
        part_start_time = time.time()
    except Exception as ex:
        tb = traceback.format_exc()
        LogEntry.add(request.user, u'error', u'Error syncing master DB: {0}({1})'.format(type(ex).__name__, ex), tb)
        return {
            'success': False,
            'error': unicode(ex),
            'traceback': tb
        }

    # try:
    # if trans_sync.sync_fulltext():
    # LogEntry.add(request.user, u'error', u'Fulltext table was out of sync. Synced.')
    # except Exception as ex:
    # tb = traceback.format_exc()
    # LogEntry.add(request.user, u'error', u'Error syncing fulltext table: {0}'.format(ex), tb)
    #     return {
    #         'success': False,
    #         'error': unicode(ex),
    #         'traceback': tb
    #     }

    time_taken = time.time() - start_time
    LogEntry.add(request.user, u'info',
                 u'Completed what.cd sync in {0:.3f}s. Profile in {1:.3f}s. Master DB in {2:.3f}s.'
                 .format(time_taken, profile_time, master_db_time))
    return {
        'success': True
    }


@login_required
@user_passes_test(lambda u: u.is_superuser is True)
@json_return_method
def sync_replicas(request):
    start_time = time.time()
    part_start_time = time.time()

    master = ReplicaSet.get_what_master()
    try:
        for replica_set in ReplicaSet.objects.all():
            if replica_set.id != master.id:
                trans_sync.sync_all_instances_db(request, replica_set)
        replicas_dbs_time = time.time() - part_start_time
    except Exception as ex:
        tb = traceback.format_exc()
        LogEntry.add(request.user, u'error', u'Error syncing replicas DB: {0}'.format(ex), tb)
        return {
            'success': False,
            'error': unicode(ex),
            'traceback': tb
        }

    try:
        trans_sync.sync_all_replicas_to_master()
    except Exception as ex:
        tb = traceback.format_exc()
        LogEntry.add(request.user, u'error', u'Error running replica sync: {0}'.format(ex), tb)
        return {
            'success': False,
            'error': unicode(ex),
            'traceback': tb
        }
    time_taken = time.time() - start_time

    LogEntry.add(request.user, u'info',
                 u'Completed replica sync in {0:.3f}s. DB in {1:.3f}s.'.format(time_taken,
                                                                               replicas_dbs_time))
    return {
        'success': True
    }


@login_required
@permission_required('home.run_checks', raise_exception=True)
@json_return_method
def checks(request):
    try:
        result = WhatManager2.checks.run_checks()
    except Exception as ex:
        tb = traceback.format_exc()
        LogEntry.add(request.user, u'error', u'Error running checks: {0}'.format(ex), tb)
        return {
            'success': False,
            'error': unicode(ex),
            'traceback': tb
        }
    result.update({
        'success': True
    })
    return result


@login_required
@require_POST
@json_return_method
@csrf_exempt
def add_torrent(request):
    if not request.user.has_perm('home.add_whattorrent'):
        return {
            'success': False,
            'error': 'You don\'t have permission to add torrents. Talk to the administrator.'
        }

    if 'dir' in request.POST:
        download_location = DownloadLocation.objects.get(
            zone=ReplicaSet.ZONE_WHAT,
            path=request.POST['dir']
        )
    else:
        download_location = DownloadLocation.get_what_preferred()

    if download_location.free_space_percent < MIN_FREE_DISK_SPACE:
        LogEntry.add(request.user, u'error', u'Failed to add torrent. Not enough disk space.')
        return {
            'success': False,
            'error': u'Not enough free space on disk.'
        }

    try:
        what_id = int(request.POST['id'])
    except ValueError:
        return {
            'success': False,
            'error': u'Invalid id'
        }

    instance = ReplicaSet.get_what_master().get_preferred_instance()

    try:
        if WhatTorrent.is_downloaded(request, what_id=what_id):
            m_torrent = TransTorrent.objects.filter(what_torrent_id=what_id)[0]
            raise TorrentAlreadyAddedException()
        m_torrent = manage_torrent.add_torrent(request, instance, download_location, what_id, True)
        m_torrent.what_torrent.added_by = request.user
        m_torrent.what_torrent.save()
    except TorrentAlreadyAddedException:
        LogEntry.add(request.user, u'info',
                     u'Tried adding what_id={0}, already added.'.format(what_id))
        what_torrent = WhatTorrent.get_or_none(request, what_id=what_id)
        return {
            'success': False,
            'error_code': u'already_added',
            'error': u'Already added.',
            'torrent_id': m_torrent.what_torrent_id,
            'artist': what_torrent.info_artist if what_torrent else '<<< Unable to find torrent >>>',
            'title': what_torrent.info_title if what_torrent else '<<< Unable to find torrent >>>',
        }
    except Exception as ex:
        tb = traceback.format_exc()
        LogEntry.add(request.user, u'error',
                     u'Tried adding what_id={0}. Error: {1}'.format(what_id, unicode(ex)), tb)
        return {
            'success': False,
            'error': unicode(ex),
            'traceback': tb,
        }

    tags = request.POST.get('tags')
    if tags:
        m_torrent.what_torrent.tags = tags
        m_torrent.what_torrent.save()

    LogEntry.add(request.user, u'action', u'Added {0} to {1}'.format(m_torrent, m_torrent.instance))

    return {
        'success': True,
        'artist': m_torrent.what_torrent.info_artist,
        'title': m_torrent.what_torrent.info_title,
    }


@login_required
@user_passes_test(lambda u: u.is_superuser is True)
@json_return_method
def update_freeleech(request):
    start_time = time.time()

    added = 0
    total_bytes = 0
    total_torrents = 0
    try:
        master = ReplicaSet.get_what_master()
        what_client = get_what_client(request)
        for what_id, what_group, what_torrent in what_client.get_free_torrent_ids():
            total_bytes += what_torrent['size']
            total_torrents += 1
            if not WhatTorrent.is_downloaded(request, what_id=what_id):
                download_locations = DownloadLocation.objects.filter(zone=ReplicaSet.ZONE_WHAT)
                download_locations = [l for l in download_locations if l.free_space_percent >= MIN_FREE_DISK_SPACE]
                if len(download_locations) == 0:
                    LogEntry.add(request.user, u'error',
                                 u'Unable to update freeleech: not enough space on disk.')
                    return {
                        'success': False,
                        'error': u'Not enough free space on disk.'
                    }
                download_location = choice(download_locations)

                instance = master.get_preferred_instance()
                m_torrent = manage_torrent.add_torrent(request, instance, download_location, what_id, True)
                m_torrent.what_torrent.tags = 'seed'
                m_torrent.what_torrent.added_by = request.user
                m_torrent.what_torrent.save()
                added += 1

                LogEntry.add(request.user, u'action',
                             u'Added freeleech {0} to {1} - {2}'.format(m_torrent, m_torrent.instance,
                                                                        download_location.path))

        log_type = u'action' if added > 0 else u'info'

        if added >= FREELEECH_EMAIL_THRESHOLD and socket.gethostname() == FREELEECH_HOSTNAME:
            send_freeleech_email(u'Added {0} freeleech torrents'.format(added))

        time_taken = time.time() - start_time
        LogEntry.add(request.user, log_type,
                     u'Successfully updated freeleech in {0:.3f}s. {1} added. {2} / {3} torrents total.'.format(
                         time_taken, added, filesizeformat(total_bytes), total_torrents))
    except Exception as ex:
        tb = traceback.format_exc()
        LogEntry.add(request.user, u'error',
                     u'Error updating freeleech: {0}({1})'.format(type(ex).__name__, unicode(ex)), tb)

    return {
        'success': True,
        'added': added
    }


@login_required
@user_passes_test(lambda u: u.is_superuser is True)
@json_return_method
def run_load_balance(request):
    torrent_count = int(request.GET['count'])
    source_instance = request.GET['source']

    instance = TransInstance.objects.get(name=source_instance)
    for i in xrange(torrent_count):
        t = choice(instance.transtorrent_set.filter(torrent_uploaded=0))
        t = manage_torrent.move_torrent(t, ReplicaSet.get_what_master().get_preferred_instance())

    return {
        'success': True
    }


@login_required
@user_passes_test(lambda u: u.is_superuser is True)
@json_return_method
def move_torrent_to_location(request):
    what_id = int(request.GET['id'])
    new_location = DownloadLocation.objects.get(zone=ReplicaSet.ZONE_WHAT, path=request.GET['path'])
    what_torrent = WhatTorrent.objects.get(id=what_id)
    trans_torrent = TransTorrent.objects.get(instance__in=ReplicaSet.get_what_master().transinstance_set.all(),
                                             what_torrent=what_torrent)

    if trans_torrent.location.id == new_location.id:
        raise Exception('Torrent is already there.')

    print 'Source is', trans_torrent.location.path
    print 'Destination is', new_location.path
    print 'Instance is', trans_torrent.instance.name
    print 'Size is', trans_torrent.torrent_size
    print 'Name is', trans_torrent.torrent_name

    client = trans_torrent.instance.client
    client.stop_torrent(trans_torrent.torrent_id)
    source_path = os.path.join(trans_torrent.location.path, unicode(what_torrent.id))
    shutil.move(source_path, new_location.path)
    client.move_torrent_data(trans_torrent.torrent_id, os.path.join(new_location.path, unicode(what_torrent.id)))
    trans_torrent.location = new_location
    trans_torrent.save()
    client.verify_torrent(trans_torrent.torrent_id)
    client.start_torrent(trans_torrent.torrent_id)
    return {
        'success': True
    }


@login_required
@json_return_method
@csrf_exempt
@permission_required('home.view_whattorrent', raise_exception=True)
def torrents_info(request):
    def get_response(id, torrent):
        response = {'id': id}
        if torrent is None:
            response['status'] = 'missing'
        elif torrent.torrent_done == 1:
            response['status'] = 'downloaded'
        else:
            response['status'] = 'downloading'
            response['progress'] = torrent.torrent_done
        return response

    ids = [int(i) for i in request.POST['ids'].split(',')]
    torrents = TransTorrent.objects.filter(what_torrent_id__in=ids)
    torrents = {t.what_torrent_id: t for t in torrents}
    for torrent in torrents.itervalues():
        if torrent.torrent_done < 1:
            torrent.sync_t_torrent()

    return [get_response(id, torrents.get(id)) for id in ids]


@login_required
@json_return_method
@user_passes_test(lambda u: u.is_superuser is True)
def what_proxy(request):
    get = dict(request.GET.lists())
    action = get['action']
    del get['action']
    if 'auth' in get:
        del get['auth']
    what = get_what_client(request)
    response = what.request(action, **get)
    return response


@login_required
@json_return_method
@user_passes_test(lambda u: u.is_superuser is True)
def refresh_whattorrent(request):
    if 'id' in request.GET:
        most_recent = WhatTorrent.objects.get(id=request.GET['id'])
    else:
        most_recent = WhatTorrent.objects.defer('torrent_file').order_by('retrieved')[0]
    most_recent_id = most_recent.id
    what = get_what_client(request)
    try:
        response = what.request('torrent', id=most_recent.id)['response']
    except RequestException as ex:
        if ex.response and type(ex.response) is dict and ex.response.get('error') == 'bad id parameter':
            try:
                TransTorrent.objects.get(instance__in=ReplicaSet.get_what_master().transinstance_set.all(),
                                         what_torrent=most_recent)
                return {
                    'success': False,
                    'id': most_recent_id,
                    'status': 'missing',
                }
            except TransTorrent.DoesNotExist:
                most_recent.delete()
                return {
                    'success': True,
                    'id': most_recent_id,
                    'status': 'deleted',
                }
        else:
            return {
                'success': False,
                'status': 'unknown request exception',
            }

    old_retrieved = most_recent.retrieved
    most_recent.info = json.dumps(response)
    most_recent.retrieved = timezone.now()
    most_recent.save()
    return {
        'success': True,
        'id': most_recent_id,
        'status': 'refreshed',
        'retrieved': unicode(old_retrieved),
    }
