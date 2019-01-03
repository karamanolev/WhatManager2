from django.conf.urls import url
from .views import (edit_upload, new_upload, skip_bibliotik, skip_what,
                         upload_cover, upload_cover_upload,
                         upload_generate_torrents, upload_to_what, uploads)

app_name = 'books'

urlpatterns = [
    url(r'^uploads$', uploads, name='uploads'),
    url(r'^uploads/new$', new_upload, name='new_upload'),
    url(r'^uploads/(\d+)/edit$', edit_upload, name='edit_upload'),
    url(r'^uploads/(\d+)/cover$', upload_cover, name='upload_cover'),
    url(r'^uploads/(\d+)/cover/upload$', upload_cover_upload, name='upload_cover_upload'),
    url(r'^uploads/(\d+)/generate_torrents$', upload_generate_torrents, name='upload_generate_torrents'),
    url(r'^uploads/(\d+)/what/upload', upload_to_what, name='upload_to_what'),
    url(r'^uploads/(\d+)/what/skip', skip_what, name='skip_what'),
    url(r'^uploads/(\d+)/bibliotik/skip', skip_bibliotik, name='skip_bibliotik'),
]
