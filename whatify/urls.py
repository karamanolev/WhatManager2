from django.conf.urls import patterns, url

urlpatterns = patterns(
    '',
    url(r'^$', 'whatify.views.index'),
    url(r'^torrent_groups/search/(.+)$', 'whatify.views.search_torrent_groups'),
    url(r'^torrent_groups/(\d+)$', 'whatify.views.get_torrent_group'),
    url(r'^artists/search/(.+)$', 'whatify.views.search_artists'),
    url(r'^artists/(\d+)$', 'whatify.views.get_artist'),
)
