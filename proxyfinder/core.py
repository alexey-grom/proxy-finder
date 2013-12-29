# encoding: utf-8

from gevent.monkey import patch_all; patch_all()

from warnings import warn
from abc import ABCMeta, abstractmethod
from json import loads
from socket import AF_INET, SOCK_STREAM
from os.path import dirname, join
from datetime import datetime, timedelta
from re import MULTILINE, findall

from django.conf import settings as django_settings
from django.db.transaction import atomic
from django.db.models import Q
from django.utils.timezone import now
from django.utils.translation import ugettext_lazy as _
from gevent import spawn, joinall
from gevent.socket import socket as gsocket
from pygeoip import GeoIP, MEMORY_CACHE
from grab import Grab
from grab.spider import Spider, Task
from grab.tools.google import build_search_url
import human_curl
import requests

from models import Proxy, Site, Url


DEFAULT_SETTINGS = {
    'SEARCH': {
        'GOOGLE_QUERIES': [
            'free proxy list',
            'http proxies',
        ],
        'GOOGLE_RESULTS_COUNT': 100,
        'SCAN_DEPTH': 3,
        'COUNT_FOR_DIPPING': 3,
        'IGNORE_IPS': [
            ['10.0.0.0', '10.255.255.255'],
            ['172.16.0.0', '172.31.255.255'],
            ['192.168.0.0 ', '192.168.255.255'],
        ],
    },
    'CHECK': {
        'PORTS': [80,
                  8080,
                  8081,
                  8181,
                  3128,
                  808,
                  8000,
                  443,
                  1080,
                  559, ],
        'ITERATE_SIZE': 10,
        'NETWORK_TIMEOUT': 5,
    }
}


class DotDict(dict):
    def __getattr__(self, item):
        if item not in self:
            raise Exception('Setting `%s` is not present!' % item)
        return self[item]


def get_settings():
    if not hasattr(django_settings, 'PROXY_FINDER'):
        warn('Working with default settings for proxy finder!')

    settings = DEFAULT_SETTINGS
    settings.update(getattr(
        django_settings,
        'PROXY_FINDER',
        {}
    ))

    return DotDict(settings)


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

                for proxy_type in Proxy.TYPE[1:]:
                    # GET
                    self.check_get_request(proxy_type, proxies)

                    # POST
                    self.check_post_request(proxy_type, proxies)

                for proxy in proxies:
                    if not proxy.type:
                        pass
                        #if proxy.pk:
                        #    proxy.delete()
                        #else:
                        #    del proxy
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
            #elif proxies[index].pk:
            #    proxies[index].delete()

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
            proxies = queryset. \
                order_by('?'). \
                all()
            proxies = proxies[:self.settings.CHECK['ITERATE_SIZE']]
            yield list(proxies)


class DirectProxyChecker(ProxyChecker):
    def __init__(self, proxies):
        super(DirectProxyChecker, self).__init__()
        self._for_check = proxies

    def proxies_iterator(self):
        count = self.settings.CHECK['ITERATE_SIZE']
        for index in xrange(0, len(self._for_check), count):
            yield self._for_check[index:index + count]


class ProxyFinder(Spider):
    def __init__(self, *args, **kwargs):
        self.settings = get_settings()

        self.ignore_ips = self.settings.SEARCH['IGNORE_IPS']
        for index, ips_range in enumerate(self.ignore_ips):
            self.ignore_ips[index] = map(Proxy.ip_to_int, ips_range)

        super(ProxyFinder, self).__init__(*args, **kwargs)

        #self.setup_cache('mongo', database='grab-cache')
        #self.setup_queue()

    def task_generator(self):
        for query in self.settings.SEARCH['GOOGLE_QUERIES']:
            grab = Grab()
            grab.setup(
                url=build_search_url(
                    query,
                    per_page=self.settings.SEARCH['GOOGLE_RESULTS_COUNT'],
                ),
                user_agent='Mozilla/4.0 (compatible; MSIE 6.01; Windows NT 6.0)',
            )
            yield Task(
                'search_result',
                grab=grab
            )

    def task_search_result(self, grab, task):
        self.process_links(
            grab=grab,
            task_name='page',
            xpath='//li[@class="g"]/h3/a/@href',
            depp_level=0
        )

    def is_ignored_ip(self, ip):
        ip = Proxy.ip_to_int(ip)
        for range_start, range_end in self.ignore_ips:
            if range_start <= ip or ip <= range_end:
                return True
        return False

    def get_unique_ips(self, grab):
        ips = findall('(\d{1,3}[.]\d{1,3}[.]\d{1,3}[.]\d{1,3}([:]\d{1,5})?)',
                      grab.response.unicode_body(),
                      flags=MULTILINE)
        ips = set(map(
            lambda address: tuple(address[0].split(':')),
            ips
        ))
        ips = filter(
            lambda address: self.is_ignored_ip(address[0]),
            ips
        )

        def prepare_ip(ip):
            ip = list(ip[:2]) + [0, ]
            ip, port = ip[:2]
            ip = Proxy.ip_to_int(ip)
            port = int(port)
            kwargs = dict(ip=ip, port=port)
            if Proxy.objects.filter(**kwargs).exists():
                return None
            return Proxy(**kwargs)

        ips = map(prepare_ip, ips)
        ips = filter(lambda ip: ip is not None, ips)

        return ips

    def get_unviewed_url(self, grab):
        domain, path = Url.split_url(grab.response.url)
        if not (domain and path):
            return

        grab.tree.make_links_absolute(grab.response.url)

        links = map(
            lambda item: unicode(item),
            grab.tree.xpath('//a/@href')
        )
        links = set(filter(
            lambda link: Url.split_url(link)[0] == domain and
                         not Url.is_exists(link),
            links
        ))

        for link in links:
            domain, path = Url.split_url(link)
            if not (domain and path):
                continue
            site, _ = Site.objects.get_or_create(domain=domain)
            url, _ = Url.objects.get_or_create(site=site,
                                               path=path)

        return links

    def task_page(self, grab, task):
        if not hasattr(task, 'level'):
            task.level = 0

        # STORE FOUND IP'S

        ips = self.get_unique_ips(grab)
        if ips:
            Proxy.objects.bulk_create(ips)

        # URL'S STATISTICS

        domain, path = Url.split_url(grab.response.url)

        if domain and path:
            site, created = Site.objects.get_or_create(domain=domain)
            url, created = Url.objects.get_or_create(site=site,
                                                     path=path)
            url.count = len(ips)
            url.save()

        # CHECKING DEPTH

        is_minimal_count = \
            len(ips) < self.settings.SEARCH['COUNT_FOR_DIPPING']
        is_maximal_deep = \
            task.level < self.settings.SEARCH['SCAN_DEPTH']

        if is_minimal_count and is_maximal_deep:
            return

        # FOLLOWING URL'S

        links = self.get_unviewed_url(grab)

        if links:
            for link in links:
                yield task.clone(
                    url=link,
                    level=task.level + 1,
                )
