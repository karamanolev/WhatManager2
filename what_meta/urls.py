from django.conf.urls import patterns, url

urlpatterns = patterns(
    '',
    url(r'^image/(.*)$', 'what_meta.views.image'),
)
