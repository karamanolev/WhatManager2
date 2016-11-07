from django.conf.urls import url

from bibliotik_json import views
from bibliotik_json import maintenance_views

urlpatterns = [
    url(r'^sync$', views.sync),
    url(r'^add/(\d+)$', views.add_torrent),
    url(r'^search$', views.search),
    url(r'^torrents_info$', views.torrents_info),
    url(r'^get_torrent_file/(\d+)$', views.get_torrent_file),
    # Maintenance views
    url(r'^refresh_oldest_torrent$', maintenance_views.refresh_oldest_torrent, name='bibliotik_json-refresh_oldest_torrent'),
    url(r'^reparse_bibliotik_pages$', maintenance_views.reparse_bibliotik_pages),
]
