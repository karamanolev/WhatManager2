from django.conf.urls import url
from .parts import (checks, downloading, error_torrents, recent_log,
                        recently_downloaded, search_torrents, stats,
                        torrent_stats)
from .views import (add_all, checks, dashboard, remove_transmission_dupes,
                        stats, torrents, userscripts, view_log)

app_name = 'home'

urlpatterns = [
    url(r'^$', dashboard, name='dashboard'),
    url(r'^torrents$', torrents, name='torrents'),
    url(r'^view_log$', view_log, name='view_log'),
    url(r'^checks$', checks, name='checks'),
    url(r'^stats$', stats, name='stats'),
    url(r'^userscripts$', userscripts, name='userscripts'),
    url(r'^add_all$', add_all, name='add_all'),
    url(r'^remove_transmission_dupes$', remove_transmission_dupes, name='remove_transmission_dupes'),

    url(r'^part/error_torrents', error_torrents, name='error_torrents'),
    url(r'^part/search_torrents', search_torrents, name='search_torrents'),
    url(r'^part/checks', checks, name='checks'),
    url(r'^part/downloading$', downloading, name='downloading'),
    url(r'^part/recently_downloaded$', recently_downloaded, name='recently_downloaded'),
    url(r'^part/recent_log$', recent_log, name='recent_log'),
    url(r'^part/torrent_stats$', torrent_stats, name='torrent_stats'),
    url(r'^part/stats$', stats, name='stats'),
]
