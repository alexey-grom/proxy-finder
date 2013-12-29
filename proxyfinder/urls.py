from datetime import timedelta

from django.conf.urls import url, patterns, include

from views import ProxiesListView


# Wire up our API using automatic URL routing.
# Additionally, we include login URLs for the browseable API.
urlpatterns = patterns('',
    #url(r'^api/', include(router.urls)),
    url(r'^$', ProxiesListView.as_view(), name='proxylist'),
)
