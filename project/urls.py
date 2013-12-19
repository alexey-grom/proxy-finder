from django.conf.urls import patterns, include, url
from django.contrib import admin; admin.autodiscover()


urlpatterns = patterns('',
    url(r'^admin/', include(admin.site.urls)),
    url(r'^api/', include('rest_framework.urls', namespace='rest_framework')),
    url(r'^', include('proxyfinder.urls')),
    url(r'^', include('django.contrib.flatpages.urls')),
)
