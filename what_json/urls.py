from django.conf.urls import url

from what_json import views

urlpatterns = [
    url(r'^checks$', views.checks),
    url(r'^add_torrent$', views.add_torrent, name='what_json-add_torrent'),
    url(r'^sync$', views.sync),
    url(r'^sync_replicas$', views.sync_replicas),
    url(r'^update_freeleech$', views.update_freeleech),
    url(r'^load_balance$', views.run_load_balance),
    url(r'^move_torrent$', views.move_torrent_to_location),
    url(r'^torrents_info$', views.torrents_info),
    url(r'^refresh_whattorrent$', views.refresh_whattorrent),
    url(r'^what_proxy$', views.what_proxy),
]
