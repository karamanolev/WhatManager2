from django.conf.urls import url

from books import views

urlpatterns = [
    url(r'^uploads$', views.uploads, name='books-uploads'),
    url(r'^uploads/new$', views.new_upload, name='books-new_upload'),
    url(r'^uploads/(\d+)/edit$', views.edit_upload, name='books-edit_upload'),
    url(r'^uploads/(\d+)/cover$', views.upload_cover, name='books-upload_cover'),
    url(r'^uploads/(\d+)/cover/upload$', views.upload_cover_upload, name='books-upload_cover_upload'),
    url(r'^uploads/(\d+)/generate_torrents$', views.upload_generate_torrents, name='books-upload_generate_torrents'),
    url(r'^uploads/(\d+)/what/upload', views.upload_to_what, name='books-upload_to_what'),
    url(r'^uploads/(\d+)/what/skip', views.skip_what, name='books-skip_what'),
    url(r'^uploads/(\d+)/bibliotik/skip', views.skip_bibliotik, name='books-skip_bibliotik'),
]
