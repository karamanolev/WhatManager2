from django.conf.urls import url
from wmqueue.views import index

app_name = 'wmqueue'

urlpatterns = [
    url(r'^$', index),
    url(r'^part/queue_stats$', queue_stats),
    url(r'^queue_pop$', queue_pop),
    url(r'^pop_remove', pop_remove),
    url(r'^do_pop$', do_pop),
    url(r'^auto_pop$', auto_pop),
    url(r'^add_artist/(.+)$', add_artist),
    url(r'^add_collage/(\d+)$', add_collage),
]
