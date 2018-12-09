from django.conf.urls import url
from qobuz2.views import (edit_upload, find_replace, index, make_torrent,
                          new_upload, prepare, seed_upload, start_download,
                          title_case, upload_cover, view_cover, view_spectral)

app_name = 'qobuz2'

urlpatterns = [
    url(r'^$', index),
    url(r'^uploads/new$', new_upload),
    url(r'^uploads/(\d+)/edit$', edit_upload),
    url(r'^uploads/(\d+)/start_download$', start_download),
    url(r'^uploads/(\d+)/title_case$', title_case),
    url(r'^uploads/(\d+)/prepare$', prepare),
    url(r'^uploads/(\d+)/spectral$', view_spectral),
    url(r'^uploads/(\d+)/make_torrent$', make_torrent),
    url(r'^uploads/(\d+)/seed$', seed_upload),
    url(r'^uploads/(\d+)/cover$', view_cover),
    url(r'^uploads/(\d+)/upload_cover$', upload_cover),
    url(r'^uploads/(\d+)/find_replace$', find_replace),
]
