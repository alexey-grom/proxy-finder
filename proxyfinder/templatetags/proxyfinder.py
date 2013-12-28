# encoding: utf-8

from django import template
from django.template.loader import get_template
from django.templatetags.static import static
from django.utils.safestring import mark_safe


register = template.Library()


@register.filter
def yesno_img(value):
    src = static('admin/img/icon-%s.gif' % (
        'yes' if value else 'no'
    ))
    return mark_safe('<img src="%s">' % src)
