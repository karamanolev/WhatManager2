from django.conf.urls import url
from django.views.generic.base import TemplateView
from .views import profile

app_name = 'what_profile'

urlpatterns = [
    url(r'^$', profile),
    url(r'^part/buffer_up_down_data$', TemplateView.as_view(template_name='buffer_up_down_data.html')),
    url(r'^part/profile_history', TemplateView.as_view(template_name='profile_history.html')),
]
