# encoding: utf-8

from json import dumps

from django import template
from django.core.urlresolvers import reverse
from django.template.loader import get_template
from django.templatetags.static import static
from django.utils.safestring import mark_safe


register = template.Library()


@register.simple_tag(takes_context=True)
def is_url(context, name, **kwargs):
    url = reverse(name, kwargs=kwargs)
    request = None
    for group in context:
        if 'request' in group:
            request = group['request']
    if request and request.path.startswith(url):
        return 'active'
    return ''


@register.filter
def yesno_img(value):
    src = static('admin/img/icon-%s.gif' % (
        'yes' if value else 'no'
    ))
    return mark_safe('<img src="%s">' % src)


@register.filter
def jsonify(items):
    return mark_safe(dumps(list(items)))
