from django.conf.urls import patterns, url

urlpatterns = patterns(
    '',
    url(r'^$', 'status.views.index'),
    url(r'^check_trans', 'status.views.check_trans'),
    url(r'^status_environment', 'status.views.status_environment'),
    url(r'^status_settings', 'status.views.status_settings'),
    url(r'^status_downloadpath', 'status.views.status_downloadpath'),
)
