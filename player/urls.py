from django.conf.urls import url

from player import views

urlpatterns = [
    url(r'^$', views.index, name='player-index'),
    url(r'^file$', views.get_file, name='player-get_file'),
    url(r'^metadata$', views.metadata, name='player-metadata'),
    url(r'^album_art', views.album_art, name='player-album_art'),
]
