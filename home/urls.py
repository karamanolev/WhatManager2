from django.conf.urls import patterns, url

urlpatterns = patterns(
    '',
    url(r'^$', 'home.views.dashboard'),
    url(r'^torrents$', 'home.views.torrents'),
    url(r'^view_log$', 'home.views.view_log'),
    url(r'^checks$', 'home.views.checks'),
    url(r'^stats$', 'home.views.stats'),
    url(r'^userscripts$', 'home.views.userscripts'),
    url(r'^add_all$', 'home.views.add_all'),
    url(r'^remove_transmission_dupes$', 'home.views.remove_transmission_dupes'),

    url(r'^part/error_torrents', 'home.parts.error_torrents'),
    url(r'^part/search_torrents', 'home.parts.search_torrents'),
    url(r'^part/checks', 'home.parts.checks'),
    url(r'^part/downloading$', 'home.parts.downloading'),
    url(r'^part/recently_downloaded$', 'home.parts.recently_downloaded'),
    url(r'^part/recent_log$', 'home.parts.recent_log'),
    url(r'^part/torrent_stats$', 'home.parts.torrent_stats'),
    url(r'^part/stats$', 'home.parts.stats'),
)
