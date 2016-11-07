from django.conf.urls import url

from bibliotik import views

urlpatterns = [
    url(r'^uploads/(\d+)/bibliotik/upload$', views.upload_book, name='bibliotik-upload_book'),
    url(r'^bibliotik/refresh_ui$', views.refresh_ui, name='bibliotik-refresh_ui'),
]
