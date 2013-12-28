# encoding: utf-8

from django.contrib.sites.models import get_current_site
from django.utils.translation import ugettext_lazy as _


class Layout(object):
    def __init__(self, request):
        super(Layout, self).__init__()
        self._values = {
            'title': _(u'Главная'),
            'sitename': get_current_site(request).name,
        }

    def get(self, key, default=None):
        return self._values.get(key, default) or default

    def set(self, key, value):
        self._values[key] = value

    @property
    def values(self):
        return self._values


def get_layout(request):
    if not hasattr(request, 'layout'):
        request.layout = Layout(request)
    return request.layout
