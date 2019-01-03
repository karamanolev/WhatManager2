from django.conf.urls import url
from .views import index, status_table, request_transcode, request_retry, update

app_name = 'what_transcode'

urlpatterns = [
    url(r'^$', index, name='index'),
    url(r'^status_table$', status_table, name='status_table'),
    url(r'^request$', request_transcode, name='request_transcode'),
    url(r'^request_retry$', request_retry, name='request_retry'),
    url(r'^update$', update, name='update'),
]
