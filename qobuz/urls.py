from django.conf.urls import url
from .views import (download_torrent_file, edit_upload, new_upload,
                         start_download_album, start_seeding,
                         upload_cover_to_whatimg, uploads, view_cover,
                         view_spectral)

app_name = 'qobuz'

urlpatterns = [
    url(r'^$', uploads, name='uploads'),
    url(r'^uploads/new$', new_upload, name='new_upload'),
    url(r'^uploads/(\d+)/edit$', edit_upload, name='edit_upload'),
    url(r'^uploads/(\d+)/start_download$', start_download_album, name='start_download_album'),
    url(r'^uploads/(\d+)/spectral$', view_spectral, name='view_spectral'),
    url(r'^uploads/(\d+)/cover$', view_cover, name='view_cover'),
    url(r'^uploads/(\d+)/cover/upload_to_whatimg$', upload_cover_to_whatimg, name='upload_cover_to_whatimg'),
    url(r'^uploads/(\d+)/download_torrent$', download_torrent_file, name='download_torrent_file'),
    url(r'^uploads/(\d+)/start_seeding$', start_seeding, name='start_seeding'),
]
