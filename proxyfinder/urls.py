from datetime import timedelta

from django.conf.urls import url, patterns, include
from django.db.models import Q
from django.utils.timezone import now
from rest_framework import viewsets, routers
from rest_framework.permissions import BasePermission
from rest_framework.renderers import JSONRenderer, BrowsableAPIRenderer
from rest_framework.serializers import (ModelSerializer,
                                        SerializerMethodField)

from models import Proxy


class ReadOnlyForAll(BasePermission):
    def has_permission(self, request, view):
        return request.method == 'GET'


class ProxySerializer(ModelSerializer):
    address = SerializerMethodField('get_address')
    checked = SerializerMethodField('get_checked')
    type = SerializerMethodField('get_type')

    def get_address(self, obj):
        return obj.address(obj.port)

    def get_checked(self, obj):
        if not obj.checked:
            return timedelta()
        return now() - obj.checked

    def get_type(self, obj):
        return Proxy.TYPE[obj.type]

    class Meta:
        fields = [
            'address',
            'country_code',
            'checked',
            'type',
        ]
        model = Proxy


# ViewSets define the view behavior.
class ProxyViewSet(viewsets.ModelViewSet):
    model = Proxy

    renderer_classes = [JSONRenderer, BrowsableAPIRenderer, ]
    permission_classes = [ReadOnlyForAll, ]
    serializer_class = ProxySerializer

    def get_queryset(self):
        queryset = super(ProxyViewSet, self).get_queryset()
        queryset = queryset.filter(Q(is_anonymously=True) &
                                   Q(is_get=True) &
                                   Q(is_post=True) &
                                   ~Q(checked=None))
        queryset = queryset.filter(type=Proxy.TYPE.index('http'))
        queryset = queryset.order_by('?')

        count = int(self.request.QUERY_PARAMS.get('count', None) or 100)
        country_code = self.request.QUERY_PARAMS.get('country_code', None)
        if country_code:
            queryset = queryset.filter(country_code=country_code)

        return queryset[:min(count, 100)]


# Routers provide an easy way of automatically determining the URL conf.
router = routers.DefaultRouter()
router.register(r'proxies', ProxyViewSet)


# Wire up our API using automatic URL routing.
# Additionally, we include login URLs for the browseable API.
urlpatterns = patterns('',
    url(r'^api/', include(router.urls)),
)
