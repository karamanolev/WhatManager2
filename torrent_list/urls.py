from django.conf.urls import patterns, url

urlpatterns = patterns(
    '',
    url(r'^$', 'torrent_list.views.index'),
)
