from django.conf.urls import patterns, url

urlpatterns = patterns(
    '',
    url(r'^search/torrent_groups/(.*)$', 'what_meta.views.search_torrent_groups'),
)
