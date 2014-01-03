from django.conf.urls import url, patterns, include
from django.views.generic import TemplateView

from views import ProxiesListView


urlpatterns = patterns('',
    url(r'^$',
        TemplateView.as_view(template_name='proxyfinder/about.html'),
        name='about'),
    url(r'^proxylist$', ProxiesListView.as_view(), name='proxylist'),
)
