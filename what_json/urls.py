from django.conf.urls import patterns, include, url

urlpatterns = patterns(
    '',
    url(r'^checks$', 'what_json.views.checks'),
    url(r'^add_torrent$', 'what_json.views.add_torrent'),
    url(r'^sync$', 'what_json.views.sync'),
    url(r'^sync_replicas$', 'what_json.views.sync_replicas'),
    url(r'^update_freeleech$', 'what_json.views.update_freeleech'),
    url(r'^load_balance$', 'what_json.views.run_load_balance'),
    url(r'^move_torrent$', 'what_json.views.move_torrent_to_location'),
    url(r'^torrents_info$', 'what_json.views.torrents_info'),
    url(r'^refresh_whattorrent$', 'what_json.views.refresh_whattorrent'),
    url(r'^what_proxy$', 'what_json.views.what_proxy'),
)
