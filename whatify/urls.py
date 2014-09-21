from django.conf.urls import patterns, url

urlpatterns = patterns(
    '',
    url(r'^$', 'whatify.views.index'),
    url(r'^search/(.+)$', 'whatify.views.search'),
    url(r'^torrent_groups/(\d+)$', 'whatify.views.get_torrent_group'),
    url(r'^torrent_groups/(\d+)/download$', 'whatify.views.download_torrent_group'),
    url(r'^torrent_groups/random$', 'whatify.views.random_torrent_groups'),
    url(r'^torrent_groups/top10$', 'whatify.views.top10_torrent_groups'),
    url(r'^artists/(\d+)$', 'whatify.views.get_artist'),
)
