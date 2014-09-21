from django.conf.urls import patterns, url

urlpatterns = patterns(
    '',
    url(r'^cached_image$', 'what_meta.views.image'),
)
