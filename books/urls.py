from django.conf.urls import patterns, url

urlpatterns = patterns(
    '',
    url(r'^uploads$', 'books.views.uploads'),
    url(r'^uploads/new$', 'books.views.new_upload'),
    url(r'^uploads/(\d+)/edit$', 'books.views.edit_upload'),
    url(r'^uploads/(\d+)/cover$', 'books.views.upload_cover'),
    url(r'^uploads/(\d+)/cover/upload$', 'books.views.upload_cover_upload'),
    url(r'^uploads/(\d+)/generate_torrents$', 'books.views.upload_generate_torrents'),
    url(r'^uploads/(\d+)/what/upload', 'books.views.upload_to_what'),
    url(r'^uploads/(\d+)/what/skip', 'books.views.skip_what'),
    url(r'^uploads/(\d+)/bibliotik/skip', 'books.views.skip_bibliotik'),
)
