from django.conf.urls import patterns, url

urlpatterns = patterns(
    '',
    url(r'^uploads/(\d+)/bibliotik/upload$', 'bibliotik.views.upload_book'),
    url(r'^bibliotik/refresh_ui$', 'bibliotik.views.refresh_ui'),
    url(r'^bibliotik/cache_worker$', 'bibliotik.views.cache_worker'),
)
