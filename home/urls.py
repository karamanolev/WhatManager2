from django.conf.urls import url
from . import views
from . import parts

app_name = 'home'

urlpatterns = [
    url(r'^$', views.dashboard, name='dashboard'),
    url(r'^torrents$', views.torrents, name='torrents'),
    url(r'^view_log$', views.view_log, name='view_log'),
    url(r'^checks$', views.checks, name='checks'),
    url(r'^stats$', views.stats, name='stats'),
    url(r'^userscripts$', views.userscripts, name='userscripts'),
    url(r'^add_all$', views.add_all, name='add_all'),
    url(r'^remove_transmission_dupes$', views.remove_transmission_dupes, name='remove_transmission_dupes'),

    url(r'^part/error_torrents', parts.error_torrents, name='error_torrents'),
    url(r'^part/search_torrents', parts.search_torrents, name='search_torrents'),
    url(r'^part/checks', parts.checks, name='part_checks'),
    url(r'^part/downloading$', parts.downloading, name='downloading'),
    url(r'^part/recently_downloaded$', parts.recently_downloaded, name='recently_downloaded'),
    url(r'^part/recent_log$', parts.recent_log, name='recent_log'),
    url(r'^part/torrent_stats$', parts.torrent_stats, name='torrent_stats'),
    url(r'^part/stats$', parts.stats, name='part_stats'),
]
