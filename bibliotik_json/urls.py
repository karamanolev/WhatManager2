from django.conf.urls import url
from django.views.generic.base import TemplateView
from .views import sync, add_torrent, search, torrents_info, get_torrent_file
from .maintenance_views import refresh_oldest_torrent, reparse_bibliotik_pages

app_name = 'bibliotik_json'

urlpatterns = [
    url(r'^sync$', sync, name='sync'),
    url(r'^add/(\d+)$', add_torrent, name='add_torrent'),
    url(r'^search$', search, name='search'),
    url(r'^torrents_info$', torrents_info, name='torrents_info'),
    url(r'^get_torrent_file/(\d+)$', get_torrent_file, name='get_torrent_file'),
    # Maintenance views
    url(r'^refresh_oldest_torrent$', refresh_oldest_torrent, name='refresh_oldest_torrent'),
    url(r'^reparse_bibliotik_pages$', reparse_bibliotik_pages, name='reparse_bibliotik_pages'),
    url(r'^cache_next$', TemplateView.as_view(template_name='cache_next.html'), name='cache_next'),
]
