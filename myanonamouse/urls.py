from django.conf.urls import url
from .views import sync, add_torrent, torrents_info, get_torrent_file

app_name = 'myanonamouse'

urlpatterns = [
    url(r'^json/sync$', sync, name='sync'),
    url(r'^json/add/(\d+)$', add_torrent, name='add_torrent'),
    url(r'^json/torrents_info$', torrents_info, name='torrents_info'),
    url(r'^json/get_torrent_file/(\d+)$', get_torrent_file, name='get_torrent_file'),
    # Maintenance views
    # url(r'^json/refresh_oldest_torrent$', refresh_oldest_torrent, name='refresh_oldest_torrent'),
    # url(r'^json/reparse_mam_pages$', reparse_mam_pages, name='reparse_mam_pages'),
]
