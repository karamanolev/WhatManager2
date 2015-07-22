from django.conf.urls import patterns, url

urlpatterns = patterns(
    '',
    url(r'^json/sync$', 'myanonamouse.views.sync'),
    url(r'^json/add/(\d+)$', 'myanonamouse.views.add_torrent'),
    url(r'^json/torrents_info$', 'myanonamouse.views.torrents_info'),
    url(r'^json/get_torrent_file/(\d+)$', 'myanonamouse.views.get_torrent_file'),
    # Maintenance views
    # url(r'^json/refresh_oldest_torrent$',
    #    'myanonamouse.maintenance_views.refresh_oldest_torrent'),
    # url(r'^json/reparse_mam_pages$', 'myanonamouse.maintenance_views.reparse_mam_pages'),
)
