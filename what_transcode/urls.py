from django.conf.urls import url

from what_transcode import views

urlpatterns = [
    url(r'^$', views.index, name='what_transcode-index'),
    url(r'^status_table$', views.status_table, name='what_transcode-status_table'),
    url(r'^request$', views.request_transcode, name='what_transcode-request_transcode'),
    url(r'^request_retry$', views.request_retry, name='what_transcode-request_retry'),
    url(r'^update$', views.update, name='what_transcode-update'),
]
