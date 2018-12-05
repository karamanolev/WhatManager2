from django.conf.urls import patterns, url

urlpatterns = patterns(
    '',
    url(r'^$', 'wmqueue.views.index'),
    url(r'^part/queue_stats$', 'wmqueue.parts.queue_stats'),
    url(r'^queue_pop$', 'wmqueue.parts.queue_pop'),
    url(r'^pop_remove', 'wmqueue.parts.pop_remove'),
    url(r'^do_pop$', 'wmqueue.parts.do_pop'),
    url(r'^auto_pop$', 'wmqueue.parts.auto_pop'),
    url(r'^add_artist/(.+)$', 'wmqueue.parts.add_artist'),
    url(r'^add_collage/(\d+)$', 'wmqueue.parts.add_collage'),
)
