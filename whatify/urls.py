from django.conf.urls import url
from .views import (download_torrent_group, get_artist,
                           get_torrent_group, index, random_torrent_groups,
                           search, top10_torrent_groups)

app_name = 'whatify'

urlpatterns = [
    url(r'^$', index),
    url(r'^search/(.+)$', search),
    url(r'^torrent_groups/(\d+)$', get_torrent_group),
    url(r'^torrent_groups/(\d+)/download$', download_torrent_group),
    url(r'^torrent_groups/random$', random_torrent_groups),
    url(r'^torrent_groups/top10$', top10_torrent_groups),
    url(r'^artists/(\d+)$', get_artist),
]
