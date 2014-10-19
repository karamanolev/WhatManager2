from django.conf.urls import patterns, include, url
from django.contrib import admin

admin.autodiscover()

urlpatterns = patterns(
    '',
    url(r'^admin/', include(admin.site.urls)),
    url(r'^', include('home.urls')),
    url(r'^json/', include('what_json.urls')),
    url(r'^download/', include('download.urls')),
    url(r'^user/', include('login.urls')),
    url(r'^queue/', include('queue.urls')),
    url(r'^profile/', include('what_profile.urls')),
    url(r'^player/', include('player.urls')),
    url(r'^transcode/', include('what_transcode.urls')),
    url(r'^books/', include('books.urls')),
    url(r'^books/', include('bibliotik.urls')),
    url(r'^books/bibliotik/json/', include('bibliotik_json.urls')),
    url(r'^userscript/', include('userscript.urls')),
    url(r'^what_meta/', include('what_meta.urls')),
    url(r'^whatify/', include('whatify.urls')),
    url(r'^status/', include('status.urls')),

)
