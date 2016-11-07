from django.conf.urls import url

from what_meta import views

urlpatterns = [
    url(r'^cached_image$', views.image, name='what_meta-image'),
]
