from django.contrib.auth.decorators import login_required, user_passes_test
from django.db import transaction
from django.utils import timezone

from WhatManager2.utils import json_return_method
from bibliotik.models import BibliotikTorrent, BibliotikTransTorrent
from bibliotik.utils import BibliotikClient
from home.models import ReplicaSet


@login_required
@json_return_method
@user_passes_test(lambda u: u.is_superuser is True)
def reparse_bibliotik_pages(request):
    torrent_count = 0
    with transaction.atomic():
        for torrent in BibliotikTorrent.objects.all():
            torrent.parse_html_page()
            torrent.save()
            torrent_count += 1
    return {
        'success': True,
        'reparsed': torrent_count
    }


@login_required
@json_return_method
@user_passes_test(lambda u: u.is_superuser is True)
def refresh_oldest_torrent(request):
    bibliotik_id = request.GET['bibliotik_id']
    bibliotik_client = BibliotikClient(bibliotik_id)
    most_recent = BibliotikTorrent.objects.defer('torrent_file').order_by('retrieved')[0]
    most_recent_id = most_recent.id
    try:
        most_recent.import_bibliotik_data(bibliotik_client)
    except Exception:
        try:
            BibliotikTransTorrent.objects.get(
                instance__in=ReplicaSet.get_bibliotik_master().transinstance_set.all(),
                bibliotik_torrent=most_recent)
            return {
                'success': False,
                'id': most_recent_id,
                'status': 'request error',
            }
        except BibliotikTransTorrent.DoesNotExist:
            most_recent.delete()
            return {
                'success': True,
                'id': most_recent_id,
                'status': 'deleted',
            }

    old_retrieved = most_recent.retrieved
    most_recent.retrieved = timezone.now()
    most_recent.save()
    return {
        'success': True,
        'id': most_recent_id,
        'status': 'refreshed',
        'retrieved': str(old_retrieved),
    }
