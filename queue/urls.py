from django.conf.urls import patterns, url

urlpatterns = patterns(
    '',
    url(r'^$', 'queue.views.index'),
    url(r'^part/queue_stats$', 'queue.parts.queue_stats'),
    url(r'^queue_pop$', 'queue.parts.queue_pop'),
    url(r'^pop_remove', 'queue.parts.pop_remove'),
    url(r'^do_pop$', 'queue.parts.do_pop'),
    url(r'^auto_pop$', 'queue.parts.auto_pop'),
    url(r'^add_artist/(.+)$', 'queue.parts.add_artist'),
    url(r'^add_collage/(\d+)$', 'queue.parts.add_collage'),
)
