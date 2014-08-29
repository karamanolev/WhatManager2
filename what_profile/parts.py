from datetime import timedelta
import time

from django.contrib.auth.decorators import login_required
from django.db import connection
from django.shortcuts import render
from django.utils import timezone

from WhatManager2.utils import json_return_method
from what_profile.models import WhatUserSnapshot


@login_required
@json_return_method
def buffer_up_down_data(request):
    since = timezone.now() - timedelta(days=5)
    snapshots = [
        (time.mktime(s[0].timetuple()) * 1000, s[1], s[2]) for s in
        WhatUserSnapshot.objects.filter(datetime__gte=since).values_list('datetime', 'uploaded', 'downloaded')
    ]
    buffer_points = []
    for snapshot in snapshots:
        buffer_points.append([
            snapshot[0],
            snapshot[1] / 1.05 - snapshot[2]
        ])
    up_points = []
    down_points = []
    prev_point = snapshots[0]
    for snapshot in snapshots:
        # Get a point every 60 minutes (with a 30 seconds buffer)
        if snapshot is snapshots[-1] or snapshot[0] - prev_point[0] >= 60 * 60 * 1000 - 30:
            up_points.append((snapshot[0], snapshot[1] - prev_point[1]))
            down_points.append((snapshot[0], snapshot[2] - prev_point[2]))
            prev_point = snapshot
    return {
        'buffer': buffer_points,
        'up': up_points,
        'down': down_points,
    }


@login_required
def profile_history(request):
    since = timezone.now() - timedelta(days=1)

    input_snapshots = [
        WhatUserSnapshot.get_closest_snapshot(when) for when in
        [since + timedelta(hours=h) for h in range(0, 25)]
    ]

    snapshots = []
    prev = None
    for snapshot in input_snapshots:
        if prev:
            snapshots.append({
                'datetime': snapshot.datetime,
                'uploaded': snapshot.uploaded - prev.uploaded,
                'total_uploaded': snapshot.uploaded,
                'downloaded': snapshot.downloaded - prev.downloaded,
                'total_downloaded': snapshot.downloaded,
                'buffer': snapshot.buffer_105 - prev.buffer_105,
                'total_buffer': snapshot.buffer_105,
                'ratio': snapshot.ratio - prev.ratio,
                'total_ratio': snapshot.ratio,
            })
            prev = snapshot
        else:
            prev = snapshot
    data = {
        'snapshots': snapshots
    }
    return render(request, 'what_profile/part_ui/profile_history.html', data)