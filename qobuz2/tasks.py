import os

from celery import task
from django.db import connection

from qobuz2.models import QobuzUpload, get_qobuz_client
from qobuz2.utils import get_temp_dir
from what_transcode.utils import recursive_chmod


@task(bind=True, track_started=True)
def qiller_download(celery_task, qobuz_album_id):
    try:
        upload = QobuzUpload.objects.get(id=qobuz_album_id)
        qiller = upload.upload
        temp_dir = get_temp_dir(qiller.metadata.id)
        qiller.download(temp_dir, True)
        upload.set_upload(qiller)
        for item in os.listdir(temp_dir):
            recursive_chmod(os.path.join(temp_dir, item), 0o777)
        upload.save()
    finally:
        connection.close()


def start_qiller_download(qobuz_upload):
    if qobuz_upload.download_task_id is not None:
        raise Exception('There is already a task assigned.')
    async_result = qiller_download.delay(qobuz_upload.id)
    print(async_result.id)
    qobuz_upload.download_task_id = async_result.id
    qobuz_upload.save()
