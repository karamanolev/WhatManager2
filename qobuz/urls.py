from django.conf.urls import patterns, url

urlpatterns = patterns(
    '',
    url(r'^$', 'qobuz.views.uploads'),
    url(r'^uploads/new$', 'qobuz.views.new_upload'),
    url(r'^uploads/(\d+)/edit$', 'qobuz.views.edit_upload'),
    url(r'^uploads/(\d+)/start_download$', 'qobuz.views.start_download_album'),
    url(r'^uploads/(\d+)/spectral$', 'qobuz.views.view_spectral'),
    url(r'^uploads/(\d+)/cover$', 'qobuz.views.view_cover'),
    url(r'^uploads/(\d+)/cover/upload_to_whatimg$', 'qobuz.views.upload_cover_to_whatimg'),
    url(r'^uploads/(\d+)/download_torrent$', 'qobuz.views.download_torrent_file'),
    url(r'^uploads/(\d+)/start_seeding$', 'qobuz.views.start_seeding'),
)
