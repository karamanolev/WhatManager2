from django.db import models

# Create your models here.
from home.models import WhatTorrent


class TranscodeRequest(models.Model):
    what_torrent = models.ForeignKey(WhatTorrent, on_delete=models.CASCADE)
    requested_by_ip = models.TextField()
    requested_by_what_user = models.TextField()
    date_requested = models.DateTimeField(auto_now_add=True)
    date_completed = models.DateTimeField(null=True)
    celery_task_id = models.TextField(null=True)
