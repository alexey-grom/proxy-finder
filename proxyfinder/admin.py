from django.contrib import admin
from django.db.models import Count, Sum, Q
from django.utils.translation import ugettext_lazy as _

from countries import country_codes
from models import Site, Url, Proxy


class CountriesListFilter(admin.SimpleListFilter):
    title = _('Country')
    parameter_name = 'country_code'

    def lookups(self, request, model_admin):
        present_country_code = Proxy.objects.\
            values('country_code').\
            annotate(count=Count('country_code')).\
            filter(count__gte=0).\
            order_by('-count')

        present_country_code = [
            item['country_code']
            for item in present_country_code
        ]

        return [
            (item, country_codes[item] if item in country_codes else item)
            for item in present_country_code
        ]

    def queryset(self, request, queryset):
        if self.value():
            queryset = queryset.filter(country_code__exact=self.value())
        return queryset


class ProxyAdmin(admin.ModelAdmin):
    fields = [
        'display_ip',
        'updated',
        'checked',
        'type',
        'is_get',
        'is_post',
        'is_anonymously',
        'country_code',
    ]
    list_display = [
        'display_ip',
        'country_code',
        'type',
        'checked',
        'is_get',
        'is_post',
        'is_anonymously',
    ]

    readonly_fields = [
        'display_ip',
        'updated',
        'checked',
        'type',
        'country_code',
        'is_get',
        'is_post',
        'is_anonymously',
    ]

    ordering = [
        'ip',
        'port',
    ]

    list_filter = [
        'is_get',
        'is_post',
        'is_anonymously',
        'type',
        CountriesListFilter,
    ]

    list_per_page = 200

    def display_ip(self, obj):
        port = None
        if obj.port:
            port = obj.port
        return obj.address(port)
    display_ip.short_description = _('IP:port')
    display_ip.admin_order_field = 'ip'


class UrlsInline(admin.StackedInline):
    model = Url

    readonly_fields = [
        'path',
        'count',
    ]

    ordering = [
        'path',
    ]


class SiteAdmin(admin.ModelAdmin):
    ordering = [
        'domain',
    ]

    list_display = [
        'domain',
        'pages_count',
        'proxies_count',
    ]

    readonly_fields = [
        'domain',
        'pages_count',
    ]

    inlines = [
        UrlsInline,
    ]

    def get_queryset(self, request):
        queryset = super(SiteAdmin, self).get_queryset(request)
        queryset = queryset.annotate(pages_count=Count('url'),
                                     proxies_count=Sum('url__count'))
        return queryset

    def pages_count(self, obj):
        return obj.pages_count
    pages_count.short_description = _('Scanned pages')

    def proxies_count(self, obj):
        return obj.proxies_count
    proxies_count.short_description = _('Finded count')


admin.site.register(Site, SiteAdmin)
admin.site.register(Url)
admin.site.register(Proxy, ProxyAdmin)
