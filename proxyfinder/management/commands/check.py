# encoding: utf-8

from gevent.monkey import patch_all; patch_all()

from abc import ABCMeta, abstractmethod
from pprint import pprint
from json import loads
from socket import AF_INET, SOCK_STREAM
from os.path import dirname, join
from datetime import datetime, timedelta

from django.core.management.base import BaseCommand, CommandError
#from django.db.transaction import commit_on_success
from django.db.transaction import atomic
from django.db.models import Q
from django.utils.timezone import now
from django.utils.translation import ugettext_lazy as _
from requests import get, post
from gevent import spawn, joinall
from gevent.socket import socket as gsocket
from pygeoip import GeoIP, MEMORY_CACHE
import human_curl
import requests

from ...models import Proxy, Site, Url
from settings import get_settings


#class ProxyInfo(object):
#    __metaclass__ = ABCMeta
#
#    def __init__(self, proxy_object):
#        self.host = host
#        self.port = port
#        self.country = None
#        self.is_up = False
#        self.types = []


class ProxyChecker(object):
    def __init__(self):
        self._local_ip = None
        self._gi4 = GeoIP(join(dirname(__file__), 'GeoIP.dat'),
                          MEMORY_CACHE)
        self.settings = get_settings()
        super(ProxyChecker, self).__init__()

    @abstractmethod
    def proxies_iterator(self):
        yield None

    def run(self):
        for proxies in self.proxies_iterator():
            with atomic():
                proxies = self.extend_addresses(proxies)

                #
                for proxy in proxies:
                    proxy.is_get = False
                    proxy.is_post = False
                    proxy.is_anonymously = False
                    proxy.country_code = None
                    proxy.type = 0

                # фильтрация только тех у которых проходит
                # подключение на порт
                proxies = self.check_opened(proxies)

                #pprint([
                #    now(),
                #])

                for proxy_type in Proxy.TYPE[1:]:
                    print 'check for type `%s`' % proxy_type

                    # GET
                    self.check_get_request(proxy_type, proxies)

                    # POST
                    self.check_post_request(proxy_type, proxies)

                    #pprint([
                    #    str(now()),
                    #    proxies
                    #])

                for proxy in proxies:
                    if not proxy.type:
                        if proxy.pk:
                            proxy.delete()
                        else:
                            del proxy
                    else:
                        proxy.country_code = self.get_country_code(
                            proxy.address()
                        )
                        proxy.checked = now()
                        proxy.save()

            #return

    def get_country_code(self, ip):
        u"""Код страны по IP"""
        return self._gi4.country_code_by_addr(ip)

    @property
    def local_ip(self):
        if not self._local_ip:
            answer = requests.get('http://httpbin.org/ip').json()
            self._local_ip = answer['origin']
        return self._local_ip

    def extend_addresses(self, proxies):
        u"""Дополнение списка проксей возможными портами"""

        additional = []

        addresses = [
            proxy.as_tuple()
            for proxy in proxies
            if proxy.port
        ]

        for port in set(self.settings.CHECK['PORTS']):
            for proxy in proxies:
                if proxy.as_tuple() in addresses:
                    continue
                if not proxy.port:
                    proxy.port = port
                else:
                    other_proxy, _ = Proxy.objects.get_or_create(
                        ip=proxy.ip,
                        port=port
                    )
                    additional.append(other_proxy)

        #_all = [
        #    proxy.as_tuple()
        #    for proxy in (proxies + additional)
        #]
        #
        #pprint([
        #    'achtung!',
        #    [
        #        (_all.count(_), _)
        #        for _ in set(_all)
        #    ]
        #])

        return proxies + additional

    def check_opened(self, proxies):
        u"""Проверка открытости порта"""

        def checker(host, port):
            try:
                s = gsocket(AF_INET, SOCK_STREAM)
                s.connect((host, port))
                s.close()
            except:
                return False
            return True

        jobs = [
            spawn(checker, proxy.address(), proxy.port)
            for proxy in proxies
        ]
        joinall(
            jobs,
            timeout=self.settings.CHECK['NETWORK_TIMEOUT']
        )

        result = []

        for index, job in enumerate(jobs):
            if job.value:
                result.append(proxies[index])
            elif proxies[index].pk:
                proxies[index].delete()

        return result

    def check_get_request(self, proxy_type, proxies):
        u"""Проверка GET-запросов"""

        URL = 'http://httpbin.org/get'
        valid = []
        anonymously = []

        def success_callback(response, async_client, opener):
            try:
                proxy = response.request._proxy[1]

                content = loads(response.content)
                is_valid = response.url == URL and \
                           'origin' in content and \
                           response.status_code == 200
                if not is_valid:
                    return
                valid.append(proxy)
                if self.local_ip not in content['origin'].split(', '):
                    anonymously.append(proxy)
            except:
                pass

        client = human_curl.AsyncClient(
            success_callback=success_callback,
            fail_callback=lambda **kwargs: None
        )

        for proxy in proxies:
            client.method(
                'GET',
                url=URL,
                timeout=self.settings.CHECK['NETWORK_TIMEOUT'],
                connection_timeout=self.settings.CHECK['NETWORK_TIMEOUT'],
                proxy=(proxy_type, proxy.as_tuple())
            )

        client.start()

        for proxy in proxies:
            if proxy.as_tuple() in valid:
                proxy.is_get = True
                proxy.type = Proxy.TYPE.index(proxy_type)

            if proxy.as_tuple() in anonymously:
                proxy.is_anonymously = True

    def check_post_request(self, proxy_type, proxies):
        u"""Проверка POST-запросов"""

        URL = 'http://httpbin.org/post'
        DATA = {
            'field1': 'value1',
            'field2': 'value2',
        }
        valid = []

        def success_callback(response, async_client, opener):
            try:
                content = loads(response.content)
                is_valid = response.url == URL and \
                           'origin' in content and \
                           response.status_code == 200 and \
                           content['form'] == DATA
                if not is_valid:
                    return
                valid.append(response.request._proxy[1])
            except:
                pass

        client = human_curl.AsyncClient(
            success_callback=success_callback,
            fail_callback=lambda **kwargs: None
        )

        for proxy in proxies:
            client.method(
                'post',
                url=URL,
                data=DATA,
                timeout=self.settings.CHECK['NETWORK_TIMEOUT'],
                connection_timeout=self.settings.CHECK['NETWORK_TIMEOUT'],
                proxy=(proxy_type, proxy.as_tuple())
            )

        client.start()

        for proxy in proxies:
            if proxy.as_tuple() in valid:
                proxy.is_post = True
                proxy.type = Proxy.TYPE.index(proxy_type)


class DBProxyChecker(ProxyChecker):
    def proxies_iterator(self):
        queryset = Proxy.objects.filter(
            Q(checked=None) |
            Q(checked__lte=now() - timedelta(days=1))
        )
        while True:
            proxies = queryset\
                .order_by('?')\
                .all()
            proxies = proxies[:self.settings.CHECK['ITERATE_SIZE']]
            yield list(proxies)


class Command(BaseCommand):
    help = _('Search proxies')

    def __init__(self, *args, **kwargs):
        super(Command, self).__init__(*args, **kwargs)
        self.settings = get_settings()

    def handle(self, *args, **options):
        try:
            checker = DBProxyChecker()
            checker.run()
        except KeyboardInterrupt:
            self.stdout.write('^Interrupt')
