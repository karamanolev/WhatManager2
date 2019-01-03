from django.conf.urls import url
from .views import login, logout, view_token

app_name = 'login'

urlpatterns = [
    url(r'^login$', login, name='login'),
    url(r'^logout$', logout, name='logout'),
    url(r'^view_token$', view_token, name='view_token'),
]
