from django.conf.urls import url
from what_json.views import (add_torrent, checks, move_torrent_to_location,
                             refresh_whattorrent, run_load_balance, sync,
                             sync_replicas, torrents_info, update_freeleech,
                             what_proxy)

app_name = 'what_json'

urlpatterns = [
    url(r'^checks$', checks),
    url(r'^add_torrent$', add_torrent),
    url(r'^sync$', sync),
    url(r'^sync_replicas$', sync_replicas),
    url(r'^update_freeleech$', update_freeleech),
    url(r'^load_balance$', run_load_balance),
    url(r'^move_torrent$', move_torrent_to_location),
    url(r'^torrents_info$', torrents_info),
    url(r'^refresh_whattorrent$', refresh_whattorrent),
    url(r'^what_proxy$', what_proxy),
]
