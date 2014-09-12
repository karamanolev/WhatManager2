from django.conf.urls import patterns, url

urlpatterns = patterns(
    '',
    url(r'^$', 'whatify.views.index'),
    url(r'^search/(.+)$', 'whatify.views.search'),
    url(r'^torrent_groups/(\d+)$', 'whatify.views.get_torrent_group'),
    url(r'^artists/(\d+)$', 'whatify.views.get_artist'),
)
