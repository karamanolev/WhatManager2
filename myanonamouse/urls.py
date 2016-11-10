from django.conf.urls import url

from myanonamouse import views

urlpatterns = [
    url(r'^json/sync$', views.sync),
    url(r'^json/add/(\d+)$', views.add_torrent),
    url(r'^json/torrents_info$', views.torrents_info),
    url(r'^json/get_torrent_file/(\d+)$', views.get_torrent_file),
    # Maintenance views
    # url(r'^json/refresh_oldest_torrent$', 'myanonamouse.maintenance_views.refresh_oldest_torrent'),
    # url(r'^json/reparse_mam_pages$', 'myanonamouse.maintenance_views.reparse_mam_pages'),
]
