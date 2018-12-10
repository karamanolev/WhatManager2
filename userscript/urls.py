from django.conf.urls import url
from .views import bibliotik, whatcd, overdrive, myanonamouse

app_name = 'userscript'

urlpatterns = [
    url(r'^bibliotik.user.js$', bibliotik),
    url(r'^what.cd.user.js$', whatcd),
    url(r'^overdrive.user.js$', overdrive),
    url(r'^myanonamouse.user.js$', myanonamouse),
]
