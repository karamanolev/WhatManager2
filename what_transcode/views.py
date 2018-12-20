# Create your views here.

import traceback

from celery import states
from celery.result import AsyncResult
from django.http.response import HttpResponse
from django.shortcuts import render
from django.template.defaultfilters import timesince_filter
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt

from WhatManager2.manage_torrent import add_torrent
from WhatManager2.settings import TRANSCODER_FORMATS
from WhatManager2.utils import json_return_method
from home.models import WhatTorrent, TransTorrent, ReplicaSet, DownloadLocation, LogEntry, \
    get_what_client
from what_transcode.tasks import transcode
from what_transcode.models import TranscodeRequest
from what_transcode.utils import get_trans_torrent, torrent_is_preemphasized, get_mp3_ids


def request_is_allowed(request):
    return (
        request.user.is_authenticated and
        request.user.is_active and
        request.user.has_perm('what_transcode.add_transcoderequest')
    )


def request_get_what_user(request):
    if request_is_allowed(request):
        if request.user.username == 'ivailo':
            return 'karamanolev'
        return request.user.username
    raise Exception('What.CD user not found')


def request_allow_retry(request):
    return request.user.is_authenticated and request.user.is_active and request.user.is_superuser


def index(request):
    allow_request = request_is_allowed(request)
    data = {
        'allow_request': allow_request,
    }
    try:
        data['what_user'] = request_get_what_user(request)
    except Exception:
        data['what_user'] = 'unknown'
    return render(request, 'what_transcode/status.html', data)


def run_transcode_task(t_r):
    async_result = transcode.delay(t_r.what_torrent_id)
    t_r.celery_task_id = async_result.id
    t_r.save()


def status_table(request):
    allow_retry = request_allow_retry(request)

    transcoding = []
    pending = []
    downloading = []
    failed = []
    succeeded = []

    def process_request(t_r):
        t_r.show_retry_button = False

        if t_r.celery_task_id is None:
            try:
                t_torrent = get_trans_torrent(t_r.what_torrent)
                t_torrent.sync_t_torrent()
                if t_torrent.torrent_done == 1:
                    t_r.status = 'download complete. transcoding should start within 1 minute.'
                else:
                    t_r.status = 'downloading ({0:.0%})'.format(t_torrent.torrent_done)
                downloading.append(t_r)
            except TransTorrent.DoesNotExist:
                t_r.status = 'torrent has been removed'
                failed.append(t_r)
        elif t_r.date_completed is not None:
            t_r.status = 'completed {0} ago'.format(timesince_filter(t_r.date_completed))
            succeeded.append(t_r)
        else:
            async_result = AsyncResult(t_r.celery_task_id)
            if async_result.state == states.PENDING:
                t_r.status = 'pending transcoding'
                pending.append(t_r)
            elif async_result.state == states.STARTED:
                t_r.status = 'transcoding'
                transcoding.append(t_r)
            elif async_result.state == 'PROGRESS':
                t_r.status = 'transcoding: {0}'.format(async_result.info['status_message'])
                transcoding.append(t_r)
            elif async_result.state == states.SUCCESS:
                t_r.status = 'completed'
                succeeded.append(t_r)
            elif async_result.state == states.FAILURE:
                t_r.show_retry_button = allow_retry
                t_r.status = 'failed - {0}({1})'.format(type(async_result.result).__name__,
                                                        async_result.result)
                failed.append(t_r)
        what_client = get_what_client(request)
        t_r.status = t_r.status.replace(what_client.authkey, '<authkey>').replace(
            what_client.passkey, '<passkey>')

    for t_request in TranscodeRequest.objects.filter(
            date_completed=None).order_by('-date_requested'):
        process_request(t_request)
    for t_request in TranscodeRequest.objects.exclude(
            date_completed=None).order_by('-date_completed')[:200]:
        process_request(t_request)

    data = {
        'requests': transcoding + pending + downloading + failed + succeeded,
    }

    return render(request, 'what_transcode/status_table.html', data)


def update(request):
    for t_r in TranscodeRequest.objects.filter(celery_task_id=None):
        t_torrent = get_trans_torrent(t_r.what_torrent)
        t_torrent.sync_t_torrent()
        if t_torrent.torrent_done == 1:
            run_transcode_task(t_r)

    for t_r in TranscodeRequest.objects.filter(date_completed=None).exclude(celery_task_id=None):
        result = AsyncResult(t_r.celery_task_id)
        if result.successful():
            t_r.date_completed = timezone.now()
            t_r.save()

    return HttpResponse('')


@json_return_method
def request_retry(request):
    if not request_allow_retry(request):
        return {
            'message': 'You must be authenticated to request retries.'
        }

    try:
        what_id = int(request.POST['what_id'])
    except:
        return {
            'message': 'Missing or invalid what id'
        }

    t_request = TranscodeRequest.objects.get(what_torrent_id=what_id)
    run_transcode_task(t_request)

    return {
        'message': 'Queued new task'
    }


@json_return_method
@csrf_exempt
def request_transcode(request):
    return run_request_transcode(request, request.POST['what_id'])


def run_request_transcode(request, what_id):
    try:
        request_what_user = request_get_what_user(request)
    except Exception:
        return {
            'message': 'You don\'t have permission to add transcode requests.'
        }

    try:
        what_id = int(what_id)
    except:
        return {
            'message': 'Missing or invalid what id'
        }

    try:
        try:
            TranscodeRequest.objects.get(what_torrent_id=what_id)
            return {
                'message': 'This has already been requested.'
            }
        except TranscodeRequest.DoesNotExist:
            pass

        what_client = get_what_client(request)

        what_torrent = WhatTorrent.get_or_create(request, what_id=what_id)
        if what_torrent.info_loads['torrent']['format'] != 'FLAC':
            return {
                'message': 'This is not a FLAC torrent. Only FLACs can be transcoded.'
            }
        if what_torrent.info_loads['torrent']['reported']:
            return {
                'message': 'You cannot add a request for a torrent that has been reported.'
            }
        if what_torrent.info_loads['torrent']['scene']:
            return {
                'message': 'Cannot transcode a scene torrent due to possible'
                           ' release group name in the file names.'
            }
        if torrent_is_preemphasized(what_torrent.info_loads):
            return {
                'message': 'This sounds as if it is pre-emphasized. Will not add request.'
            }

        group = what_client.request('torrentgroup',
                                    id=what_torrent.info_loads['group']['id'])['response']

        mp3_ids = get_mp3_ids(group, what_torrent.info_loads)

        if all(f in mp3_ids for f in TRANSCODER_FORMATS):
            return {
                'message': 'This torrent already has all the formats: {0}.'.format(
                    ', '.join(TRANSCODER_FORMATS)
                )
            }

        transcode_request = TranscodeRequest(
            what_torrent=what_torrent,
            requested_by_ip=request.META['REMOTE_ADDR'],
            requested_by_what_user=request_what_user,
        )
        transcode_request.save()

        try:
            get_trans_torrent(what_torrent)
        except TransTorrent.DoesNotExist:
            instance = ReplicaSet.get_what_master().get_preferred_instance()
            download_location = DownloadLocation.get_what_preferred()
            m_torrent = add_torrent(request, instance, download_location, what_id)
            if request.user.is_authenticated:
                m_torrent.what_torrent.added_by = request.user
            else:
                m_torrent.what_torrent.added_by = None
            m_torrent.what_torrent.tags = 'transcode'
            m_torrent.what_torrent.save()

            if request.user.is_authenticated:
                log_user = request.user
            else:
                log_user = None
            LogEntry.add(log_user, 'action', 'Transcode What.CD user {0} added {1} to {2}'
                         .format(request_what_user, m_torrent, m_torrent.instance))

        return {
            'message': 'Request added.',
        }
    except Exception as ex:
        tb = traceback.format_exc()
        if request.user.is_authenticated:
            current_user = request.user
        else:
            current_user = None
        LogEntry.add(current_user, 'error', 'What user {0} tried adding what_id {1}. Error: {2}'
                     .format(request_what_user, what_id, ex), tb)
        return {
            'message': 'Error adding request: ' + str(ex)
        }
