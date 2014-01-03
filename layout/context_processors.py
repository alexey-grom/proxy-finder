# encoding: utf-8

from django.contrib.sites.models import get_current_site
from django.utils.functional import SimpleLazyObject


def current_site(request):
    return {
        'site': SimpleLazyObject(lambda: get_current_site(request))
    }
