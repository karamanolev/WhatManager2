from django.conf.urls import url
from .views import index, get_file, metadata, album_art

app_name = 'player'

urlpatterns = [
    url(r'^$', index, name='index'),
    url(r'^file$', get_file, name='get_file'),
    url(r'^metadata$', metadata, name='metadata'),
    url(r'^album_art', album_art, name='album_art'),
]
