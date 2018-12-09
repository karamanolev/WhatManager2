from django.conf.urls import url
from what_profile.views import profile, buffer_up_down_data, profile_history

app_name = 'what_profile'

urlpatterns = [
    url(r'^$', profile),
    url(r'^part/buffer_up_down_data$', buffer_up_down_data),
    url(r'^part/profile_history', profile_history),
]
