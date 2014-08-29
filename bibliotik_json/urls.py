from django.conf.urls import patterns, url

urlpatterns = patterns(
    '',
    url(r'^sync$', 'bibliotik_json.views.sync'),
    url(r'^add/(\d+)$', 'bibliotik_json.views.add_torrent'),
    url(r'^search$', 'bibliotik_json.views.search'),
    url(r'^torrents_info$', 'bibliotik_json.views.torrents_info'),
    url(r'^get_torrent_file/(\d+)$', 'bibliotik_json.views.get_torrent_file'),
    # Maintenance views
    url(r'^refresh_oldest_torrent$', 'bibliotik_json.maintenance_views.refresh_oldest_torrent'),
    url(r'^reparse_bibliotik_pages$', 'bibliotik_json.maintenance_views.reparse_bibliotik_pages'),
)
