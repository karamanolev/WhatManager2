from django.conf.urls import url
from .views import image

app_name = 'what_meta'

urlpatterns = [
    url(r'^cached_image$', image, name='image'),
]
