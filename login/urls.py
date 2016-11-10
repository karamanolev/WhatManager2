from django.conf.urls import url

from login import views

urlpatterns = [
    url(r'^login$', views.login, name='login-login'),
    url(r'^logout$', views.logout, name='login-logout'),
    url(r'^view_token$', views.view_token, name='login-view_token'),
]
