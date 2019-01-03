from django.conf.urls import url
from .views import bibliotik, whatcd, overdrive, myanonamouse

app_name = 'userscript'

urlpatterns = [
    url(r'^bibliotik.user.js$', bibliotik, name='bibliotik'),
    url(r'^what.cd.user.js$', whatcd, name='whatcd'),
    url(r'^overdrive.user.js$', overdrive, name='overdrive'),
    url(r'^myanonamouse.user.js$', myanonamouse, name='myanonamouse'),
]
