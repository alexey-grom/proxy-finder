# encoding: utf-8

from gevent.monkey import patch_all; patch_all()

from pprint import pprint
from json import loads
from socket import AF_INET, SOCK_STREAM
from os.path import dirname, join
from datetime import datetime, timedelta

from django.core.management.base import BaseCommand, CommandError
from django.db.transaction import commit_on_success
from django.db.models import Q
from django.utils.timezone import now
from requests import get, post
from grab import Grab
# import human_curl as hurl
# from requesocks import get, post
from gevent import spawn, joinall
from gevent.socket import socket
from pygeoip import GeoIP, MEMORY_CACHE

from ...models import Proxy, Site, Url


gi4 = GeoIP(join(dirname(__file__), 'GeoIP.dat'), MEMORY_CACHE)


def get_country_code(ip):
    u"""Код страны по IP"""
    return gi4.country_code_by_addr(ip)


def get_ip():
    u"""Возвращает свой IP"""
    if not hasattr(get_ip, '__result'):
        answer = get('http://httpbin.org/ip').json()
        get_ip.__result = answer['origin']
    return get_ip.__result


def check_opened(host, port):
    u"""Проверка открытости порта"""
    try:
        s = socket(AF_INET, SOCK_STREAM)
        s.connect((host, port))
        s.close()
    except:
        return False
    return True


class Checkers:
    u""""""

    def __init__(self, proxy_type):
        self.proxy_type = proxy_type

    def _make_proxy(self, host, port):
        u""""""
        address = self.proxy_type + '://' + host + ':' + str(port)
        return {
            'http': address,
        }

    def check_anonymouse(self, host, port):
        u""""""
        URL = 'http://httpbin.org/ip'
        try:
            response = get(URL,
                           proxies=self._make_proxy(host, port))
            result = response.json()
            return response.url == URL and \
                   (get_ip() not in result['origin'].split(', '))
        except:
            pass
        return False

    def check_get_request(self, host, port):
        u""""""
        URL = 'http://httpbin.org/ip'
        try:
            response = get(URL,
                           proxies=self._make_proxy(host, port))
            result = response.json()
            return response.url == URL and response.status_code == 200 and 'origin' in result
        except:
            pass
        return False

    def check_post_request(self, host, port):
        u""""""
        URL = 'http://httpbin.org/post'
        data = {
            'field1': 'value1',
            'field2': 'value2',
        }
        try:
            response = post(URL,
                            data=data,
                            proxies=self._make_proxy(host, port))
            result = response.json()
            return response.url == URL and result['form'] == data
        except:
            pass
        return False


class Command(BaseCommand):
    help = 'Search proxies'

    PORTS = [80, 8080, 8081, 8181, 3128, 808, 8000, ]
    ITERATE_SIZE = 10
    CONNECTION_TIMEOUT = 5

    def remove_addresses(self, addresses):
        pass

    def split_valid(self, addresses, jobs):
        valid = [
            address
            for index, address in enumerate(addresses)
            if jobs[index].value
        ]
        invalid = [
            address
            for index, address in enumerate(addresses)
            if not jobs[index].value
        ]
        return valid, invalid

    def check_working(self, func, addresses):
        jobs = [
            spawn(func, *(host, port, ))
            for host, port in addresses
        ]
        joinall(jobs, timeout=self.CONNECTION_TIMEOUT)
        return self.split_valid(addresses, jobs)

    @commit_on_success
    def check_addresses(self, proxies):
        u"""Проверка списка проксей по всем типам проксей"""

        results = {}

        # расширение адресов дополнительными портами
        addresses = []
        for proxy in proxies:
            if proxy.port:
                addresses.append((proxy.address(), proxy.port, ))
            addresses.extend([
                (proxy.address(), port, )
                for port in self.PORTS
            ])

        # IS UP
        print 'checking up'
        is_up, down_hosts = self.check_working(check_opened, addresses)
        #
        for host, port in down_hosts:
            Proxy.objects.filter(ip=Proxy.ip_to_int(host), port=port).delete()
        #
        for address in is_up:
            results[address] = {
                'is_up': True,
                'type': Proxy.TYPE[0],
                'get': False,
                'post': False,
                'anonymously': False,
            }

        #
        for proxy_type in Proxy.TYPE[1:]:
            checkers = Checkers(proxy_type)

            # GET
            print 'checking GET', proxy_type
            with_get, no_get = self.check_working(checkers.check_get_request, is_up)
            if not with_get:
                continue
            for address in with_get:
                results[address]['type'] = proxy_type
                results[address]['get'] = True

            # POST
            print 'checking POST', proxy_type
            with_post, no_post = self.check_working(checkers.check_post_request, with_get)
            for address in with_post:
                results[address]['post'] = True

            # ANONYMOUSE
            print 'checking anonymously', proxy_type
            anonymously, not_anonymously = self.check_working(checkers.check_anonymouse, with_get)
            for address in anonymously:
                results[address]['anonymously'] = True

            pprint([
                (address, data)
                for address, data in results.iteritems()
                if data['type'] == proxy_type
            ])

        #
        for address, data in results.iteritems():
            host, port = address
            proxy, created = Proxy.objects.get_or_create(
                ip=Proxy.ip_to_int(host),
                port=port
            )
            proxy.is_get = data['get']
            proxy.is_post = data['post']
            proxy.is_anonymously = data['anonymously']
            proxy.type = Proxy.TYPE.index(data['type'])
            proxy.country_code = get_country_code(proxy.address())
            proxy.checked = now()
            proxy.save()

        pprint(results)

    def yield_per(self, queryset, size):
        u"""Генерация пачками по size"""
        chunk = []
        for item in queryset.all():
            chunk.append(item)
            while len(chunk) >= size:
                yield chunk[:size]
                chunk = chunk[size:]
        if chunk:
            yield chunk

    def handle(self, *args, **options):
        try:
            # перебор рабочих хостов пачками и проверка проксей
            queryset = Proxy.objects.filter(Q(checked=None) |
                                            Q(checked__lte=now() - timedelta(days=1)))
            for proxies in self.yield_per(queryset,
                                          self.ITERATE_SIZE):
                self.check_addresses(proxies)
        except KeyboardInterrupt:
            self.stdout.write('^Interrupt')
