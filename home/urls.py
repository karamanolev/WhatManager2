from django.conf.urls import url
from home.parts import (checks, downloading, error_torrents, recent_log,
                        recently_downloaded, search_torrents, stats,
                        torrent_stats)
from home.views import (add_all, checks, dashboard, remove_transmission_dupes,
                        stats, torrents, userscripts, view_log)

app_name = 'home'

urlpatterns = [
    url(r'^$', dashboard),
    url(r'^torrents$', torrents),
    url(r'^view_log$', view_log),
    url(r'^checks$', checks),
    url(r'^stats$', stats),
    url(r'^userscripts$', userscripts),
    url(r'^add_all$', add_all),
    url(r'^remove_transmission_dupes$', remove_transmission_dupes),

    url(r'^part/error_torrents', error_torrents),
    url(r'^part/search_torrents', search_torrents),
    url(r'^part/checks', checks),
    url(r'^part/downloading$', downloading),
    url(r'^part/recently_downloaded$', recently_downloaded),
    url(r'^part/recent_log$', recent_log),
    url(r'^part/torrent_stats$', torrent_stats),
    url(r'^part/stats$', stats),
]
