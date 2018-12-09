from django.conf.urls import url
from bibliotik.views import upload_book, refresh_ui, cache_worker

app_name = 'bibliotik'

urlpatterns = [
    url(r'^uploads/(\d+)/bibliotik/upload$', upload_book),
    url(r'^bibliotik/refresh_ui$', refresh_ui),
    url(r'^bibliotik/cache_worker$', cache_worker),
]
