from django.conf.urls import url
from .views import upload_book, refresh_ui, cache_worker

app_name = 'bibliotik'

urlpatterns = [
    url(r'^uploads/(\d+)/bibliotik/upload$', upload_book, name='upload_book'),
    url(r'^bibliotik/refresh_ui$', refresh_ui, name='refresh_ui'),
    url(r'^bibliotik/cache_worker$', cache_worker, name='cache_worker'),
]
