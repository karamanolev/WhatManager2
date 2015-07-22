from django.conf.urls import patterns, url

urlpatterns = patterns(
    '',
    url(r'^$', 'what_transcode.views.index'),
    url(r'^status_table$', 'what_transcode.views.status_table'),
    url(r'^request$', 'what_transcode.views.request_transcode'),
    url(r'^request_retry$', 'what_transcode.views.request_retry'),
    url(r'^update$', 'what_transcode.views.update'),
    url(r'^request_delete$', 'what_transcode.views.request_delete'),
)
