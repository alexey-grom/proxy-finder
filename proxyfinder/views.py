from django.views.generic import ListView
#from crispy_forms.bootstrap import FormActions
from django_filters import FilterSet
from django_filters.views import BaseFilterView

from models import Proxy


class ProxiesFilter(FilterSet):
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
        order_by('-quality').\
        filter(type__gt=0)

    template_name = 'proxyfinder/list.html'
    paginate_by = 50
