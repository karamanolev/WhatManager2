from django.conf.urls import url
from what_meta.views import image

urlpatterns = [
    url(r'^cached_image$', image),
]
