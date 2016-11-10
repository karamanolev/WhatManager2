from django.conf.urls import url

from home import views
from home import parts

urlpatterns = [
    url(r'^$', views.dashboard, name='home-dashboard'),
    url(r'^torrents$', views.torrents, name='home-torrents'),
    url(r'^view_log$', views.view_log, name='home-view_log'),
    url(r'^checks$', views.checks, name='home-checks-view'),
    url(r'^stats$', views.stats, name='home-stats-view'),
    url(r'^userscripts$', views.userscripts, name='home-userscripts'),
    url(r'^add_all$', views.add_all, name='home-add_all'),
    url(r'^remove_transmission_dupes$', views.remove_transmission_dupes, name='home-remove_transmission_dupes'),

    url(r'^part/error_torrents', parts.error_torrents, name='home-error_torrents'),
    url(r'^part/search_torrents', parts.search_torrents, name='home-search_torrents'),
    url(r'^part/checks', parts.checks, name='home-checks-part'),
    url(r'^part/downloading$', parts.downloading, name='home-downloading'),
    url(r'^part/recently_downloaded$', parts.recently_downloaded, name='home-recently_downloaded'),
    url(r'^part/recent_log$', parts.recent_log, name='home-recent_log'),
    url(r'^part/torrent_stats$', parts.torrent_stats, name='home-torrent_stats'),
    url(r'^part/stats$', parts.stats, name='home-stats-part'),
]
