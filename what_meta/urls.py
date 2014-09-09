from django.conf.urls import patterns, url

urlpatterns = patterns(
    '',
    url(r'^torrent_groups/search/(.+)$', 'what_meta.views.search_torrent_groups'),
    url(r'^torrent_groups/(\d+)$', 'what_meta.views.get_torrent_group'),
)
