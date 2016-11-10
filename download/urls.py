from django.conf.urls import url

from download import views

urlpatterns = [
    url(r'^zip/(\d+)$', views.download_zip, name='download-download_zip'),
    url(r'^zip/bibliotik/(\d+)$', views.download_bibliotik_zip, name='download-download_bibliotik_zip'),
    url(r'^pls/(.+)$', views.download_pls, name='download-download_pls'),
]
