from django.conf.urls import patterns, url

urlpatterns = patterns(
    '',
    url(r'^$', 'player.views.index'),
    url(r'^file$', 'player.views.get_file'),
    url(r'^metadata$', 'player.views.metadata'),
    url(r'^album_art', 'player.views.album_art'),
)
