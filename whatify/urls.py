from django.conf.urls import url

from whatify import views

urlpatterns = [
    url(r'^$', views.index, name='whatify-index'),
    url(r'^search/(.+)$', views.search, name='whatify-search'),
    url(r'^torrent_groups/(\d+)$', views.get_torrent_group, name='whatify-get_torrent_group'),
    url(r'^torrent_groups/(\d+)/download$', views.download_torrent_group, name='whatify-download_torrent_group'),
    url(r'^torrent_groups/random$', views.random_torrent_groups, name='whatify-index'),
    url(r'^torrent_groups/top10$', views.top10_torrent_groups, name='whatify-index'),
    url(r'^artists/(\d+)$', views.get_artist, name='whatify-index'),
]
