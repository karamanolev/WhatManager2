from django.conf.urls import patterns, url

urlpatterns = patterns(
    '',
    url(r'^login$', 'login.views.login'),
    url(r'^logout$', 'login.views.logout'),
    url(r'^view_token$', 'login.views.view_token'),
)