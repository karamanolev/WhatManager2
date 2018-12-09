from django.conf.urls import url
from player.views import index, get_file, metadata, album_art

urlpatterns = [
    url(r'^$', index),
    url(r'^file$', get_file),
    url(r'^metadata$', metadata),
    url(r'^album_art', album_art),
]
