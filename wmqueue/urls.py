from django.conf.urls import url
from django.views.generic.base import TemplateView
from .views import index

app_name = 'wmqueue'

urlpatterns = [
    url(r'^$', index, name=''),
    url(r'^part/queue_stats$', TemplateView.as_view(template_name='queue_stats.html'), name=''),
    url(r'^queue_pop$', TemplateView.as_view(template_name='queue_pop.html'), name=''),
    url(r'^pop_remove', TemplateView.as_view(template_name='pop_remove.html'), name=''),
    url(r'^do_pop$', TemplateView.as_view(template_name='do_pop.html'), name=''),
    url(r'^auto_pop$', TemplateView.as_view(template_name='auto_pop.html'), name=''),
    url(r'^add_artist/(.+)$', TemplateView.as_view(template_name='add_artist.html'), name=''),
    url(r'^add_collage/(\d+)$', TemplateView.as_view(template_name='add_collage.html'), name=''),
]
