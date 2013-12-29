from django.views.generic import ListView
from django.forms import NullBooleanSelect
from django.utils.translation import ugettext_lazy as _
from django_filters import FilterSet, ChoiceFilter, BooleanFilter
from django_filters.views import BaseFilterView
from django.views.decorators.cache import cache_page
from django.utils.decorators import method_decorator

from models import Proxy


class AnyBooleanSelect(NullBooleanSelect):
    def __init__(self, *args, **kwargs):
        super(AnyBooleanSelect, self).__init__(*args, **kwargs)
        self.choices = (('1', _('Any')),
                        ('2', _('Yes')),
                        ('3', _('No')))


def field_choices_with_all(model, field_name,
                           all_label=_('All'),
                           make_sort=False,
                           filterer=None):
    choices = model._meta.get_field(field_name).choices
    if filterer and callable(filterer):
        choices = filterer(choices)
    if make_sort:
        choices = sorted(choices, key=lambda item: item[1])
    return [('', all_label)] + choices


class ProxiesFilter(FilterSet):
    type = ChoiceFilter(
        label=_('Proxy type'),
        choices=field_choices_with_all(
            Proxy,
            'type',
            _('Any')
        )
    )
    is_get = BooleanFilter(
        label=Proxy._meta.get_field('is_get').verbose_name,
        widget=AnyBooleanSelect
    )
    is_post = BooleanFilter(
        label=Proxy._meta.get_field('is_post').verbose_name,
        widget=AnyBooleanSelect
    )
    is_anonymously = BooleanFilter(
        label=Proxy._meta.get_field('is_anonymously').verbose_name,
        widget=AnyBooleanSelect
    )
    country_code = ChoiceFilter(
        label=_('Country'),
        choices=field_choices_with_all(
            Proxy,
            'country_code',
            make_sort=True
        )
    )

    class Meta:
        model = Proxy
        fields = [
            'type',
            'is_get',
            'is_post',
            'is_anonymously',
            'country_code',
        ]


class ProxiesListView(BaseFilterView, ListView):
    filterset_class = ProxiesFilter
    queryset = Proxy.quality.\
        filter(type__gt=0).\
        order_by('-quality')

    template_name = 'proxyfinder/list.html'
    paginate_by = 50

    @method_decorator(cache_page(60))
    def dispatch(self, request, *args, **kwargs):
        return super(ProxiesListView, self).dispatch(request,
                                                     *args,
                                                     **kwargs)
