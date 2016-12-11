from django.conf.urls import patterns, url

urlpatterns = patterns(
    '',
    url(r'^$', 'qobuz2.views.index'),
    url(r'^uploads/new$', 'qobuz2.views.new_upload'),
    url(r'^uploads/(\d+)/edit$', 'qobuz2.views.edit_upload'),
    url(r'^uploads/(\d+)/start_download$', 'qobuz2.views.start_download'),
    url(r'^uploads/(\d+)/title_case$', 'qobuz2.views.title_case'),
    url(r'^uploads/(\d+)/prepare$', 'qobuz2.views.prepare'),
    url(r'^uploads/(\d+)/spectral$', 'qobuz2.views.view_spectral'),
    url(r'^uploads/(\d+)/make_torrent$', 'qobuz2.views.make_torrent'),
    url(r'^uploads/(\d+)/seed$', 'qobuz2.views.seed_upload'),
    url(r'^uploads/(\d+)/cover$', 'qobuz2.views.view_cover'),
    url(r'^uploads/(\d+)/upload_cover$', 'qobuz2.views.upload_cover'),
    url(r'^uploads/(\d+)/find_replace$', 'qobuz2.views.find_replace'),
)
