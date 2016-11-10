from django.conf.urls import url

from queue import views
from queue import parts

urlpatterns = [
    url(r'^$', views.index, name='queue-index'),
    url(r'^part/queue_stats$', parts.queue_stats, name='queue-queue_stats'),
    url(r'^queue_pop$', parts.queue_pop, name='queue-queue_pop'),
    url(r'^pop_remove', parts.pop_remove, name='queue-pop_remove'),
    url(r'^do_pop$', parts.do_pop, name='queue-do_pop'),
    url(r'^auto_pop$', parts.auto_pop, name='queue-auto_pop'),
    url(r'^add_artist/(.+)$', parts.add_artist, name='queue-add_artist'),
    url(r'^add_collage/(\d+)$', parts.add_collage, name='queue-add_collage'),
]
