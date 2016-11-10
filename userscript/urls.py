from django.conf.urls import url

from userscript import views

urlpatterns = [
    url(r'^bibliotik.user.js$', views.bibliotik, name='userscript-bibliotik'),
    url(r'^what.cd.user.js$', views.whatcd, name='userscript-whatcd'),
    url(r'^overdrive.user.js$', views.overdrive, name='userscript-overdrive'),
    url(r'^myanonamouse.user.js$', views.myanonamouse, name='userscript-myanonamouse'),
]
