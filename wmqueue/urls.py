from django.conf.urls import url
from django.views.generic.base import TemplateView
from .views import index
from wmqueue import parts

app_name = 'wmqueue'

urlpatterns = [
    url(r'^$', index, name='index'),
    url(r'^part/queue_stats$', parts.queue_stats, name='queue_stats'),
    url(r'^queue_pop$', parts.queue_pop, name='queue_pop'),
    url(r'^pop_remove', parts.pop_remove, name='pop_remove'),
    url(r'^do_pop$', parts.do_pop, name='do_pop'),
    url(r'^auto_pop$', parts.auto_pop, name='auto_pop'),
    url(r'^add_artist/(.+)$', parts.add_artist, name='add_artist'),
    url(r'^add_collage/(\d+)$', parts.add_collage, name='add_collage'),
]
