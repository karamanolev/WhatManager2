import json

from django.db import models
from django.utils import timezone
from django.utils.functional import cached_property


class WhatUserSnapshot(models.Model):
    user_id = models.IntegerField()
    datetime = models.DateTimeField(auto_now_add=True, db_index=True)
    uploaded = models.BigIntegerField()
    downloaded = models.BigIntegerField()
    info = models.TextField()

    @cached_property
    def buffer_105(self):
        return self.uploaded / 1.05 - self.downloaded

    @cached_property
    def ratio(self):
        return float(self.uploaded) / self.downloaded

    @classmethod
    def get(cls, what_client, user_id):
        data = what_client.request('user', id=user_id)['response']
        return WhatUserSnapshot(
            user_id=user_id,
            uploaded=int(data['stats']['uploaded']),
            downloaded=int(data['stats']['downloaded']),
            info=json.dumps(data),
        )

    @classmethod
    def get_last(cls):
        snapshots = WhatUserSnapshot.objects.order_by('-datetime')[:1]
        if len(snapshots):
            return snapshots[0]
        raise WhatUserSnapshot.DoesNotExist()

    @classmethod
    def get_closest_snapshot(self, when):
        snapshots = WhatUserSnapshot.objects.extra(select={
            'delta': 'ABS(TIMESTAMPDIFF(SECOND, datetime, %s))'
        }, order_by=['delta'], select_params=[when])[:1]
        if len(snapshots):
            return snapshots[0]
        raise WhatUserSnapshot.DoesNotExist()

    @classmethod
    def buffer_delta(cls, delta):
        old_snapshot = cls.get_closest_snapshot(timezone.now() - delta)
        new_snapshot = cls.get_last()
        return new_snapshot.buffer_105 - old_snapshot.buffer_105
