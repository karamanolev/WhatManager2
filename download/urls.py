from django.conf.urls import patterns, url

urlpatterns = patterns(
    '',
    url(r'^zip/(\d+)$', 'download.views.download_zip'),
    url(r'^zip/bibliotik/(\d+)$', 'download.views.download_bibliotik_zip'),
    url(r'^pls/(.+)$', 'download.views.download_pls'),
)