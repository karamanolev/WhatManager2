from django.conf.urls import url
from download.views import download_zip, download_bibliotik_zip, download_pls, delete_torrent

app_name = 'download'

urlpatterns = [
    url(r'^zip/(\d+)$', download_zip),
    url(r'^zip/bibliotik/(\d+)$', download_bibliotik_zip),
    url(r'^pls/(.+)$', download_pls),
    url(r'^delete/(\d+)$', delete_torrent),
]
