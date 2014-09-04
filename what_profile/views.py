import datetime

from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from what_profile.models import WhatUserSnapshot


@login_required
def profile(request):
    if WhatUserSnapshot.objects.count():
        data = {
            'delta_hour': WhatUserSnapshot.buffer_delta(datetime.timedelta(hours=1)),
            'delta_day': WhatUserSnapshot.buffer_delta(datetime.timedelta(days=1)),
            'delta_week': WhatUserSnapshot.buffer_delta(datetime.timedelta(days=7)),
            'delta_month': WhatUserSnapshot.buffer_delta(datetime.timedelta(days=30)),
            'buffer': WhatUserSnapshot.get_last().buffer_105,
        }
    else:
        data = {
            'delta_hour': '-',
            'delta_day': '-',
            'delta_week': '-',
            'delta_month': '-',
            'buffer': '-',
        }
    return render(request, 'what_profile/profile.html', data)
