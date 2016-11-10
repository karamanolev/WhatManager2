from django.conf.urls import url

from what_profile.views import profile
from what_profile import parts

urlpatterns = [
    url(r'^$', profile, name='what_profile-profile'),
    url(r'^part/buffer_up_down_data$', parts.buffer_up_down_data, name='what_profile-buffer_up_down_data'),
    url(r'^part/profile_history', parts.profile_history, name='what_profile-profile_history'),
]
