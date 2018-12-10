from django.conf.urls import url
from django.views.generic.base import TemplateView
from .views import profile
from .parts import buffer_up_down_data, profile_history

app_name = 'what_profile'

urlpatterns = [
    url(r'^$', profile, name='profile'),
    url(r'^part/buffer_up_down_data$', buffer_up_down_data, name='buffer_up_down_data'),
    url(r'^part/profile_history', profile_history, name='profile_history'),
]
