from django.conf.urls import patterns, url

urlpatterns = patterns(
    '',
    url(r'^bibliotik.user.js$', 'userscript.views.bibliotik'),
    url(r'^what.cd.user.js$', 'userscript.views.whatcd'),
    url(r'^overdrive.user.js$', 'userscript.views.overdrive'),
)
