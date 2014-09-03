from django.conf.urls import patterns, url

urlpatterns = patterns(
    '',
    url(r'^$', 'what_profile.views.profile'),
    url(r'^part/buffer_up_down_data$', 'what_profile.parts.buffer_up_down_data'),
    url(r'^part/profile_history', 'what_profile.parts.profile_history'),
)
