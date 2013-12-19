# coding: utf

from re import MULTILINE, findall
from urlparse import urlparse

from django.core.management.base import BaseCommand, CommandError
from django.db.transaction import commit_on_success
from grab import Grab
from grab.spider import Spider, Task
from grab.tools.google import build_search_url

from ...models import Proxy, Site, Url


def split_url(url):
    domain = urlparse(url).hostname
    path = domain.join(url.split(domain)[1:])
    return domain, path


class ProxyFinder(Spider):
    google_search_queries = [
        'free proxy list',
    ]
    google_results_count = 50
    scan_deep = 3
    count_for_deep_scan = 10

    ignore_ips = [
        ['10.0.0.0', '10.255.255.255'],
        ['172.16.0.0', '172.31.255.255'],
        ['192.168.0.0 ', '192.168.255.255'],
    ]

    def __init__(self, *args, **kwargs):
        for index, ips_range in enumerate(self.ignore_ips):
            self.ignore_ips[index] = map(Proxy.ip_to_int, ips_range)

        super(ProxyFinder, self).__init__(*args, **kwargs)
        self.setup_cache('mongo', database='grab-cache')
        self.setup_queue()

    def task_generator(self):
        for query in self.google_search_queries:
            grab = Grab()
            grab.setup(
                url=build_search_url(
                    query,
                    per_page=self.google_results_count,
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

    @commit_on_success
    def task_page(self, grab, task):
        if not hasattr(task, 'level'):
            task.level = 0

        domain, path = split_url(grab.response.url)
        print domain, path

        # поиск ip-адресов
        ips = []
        try:
            ips = findall('(\d{1,3}[.]\d{1,3}[.]\d{1,3}[.]\d{1,3}([:]\d{1,5})?)',
                          grab.response.unicode_body(),
                          flags=MULTILINE)
            ips = map(
                lambda address: address[0].split(':'),
                ips
            )
            ips = filter(
                lambda address: self.is_ignored_ip(address[0]),
                ips
            )
        except:
            pass

        # сохранение ip-адресов
        for ip in ips:
            ip = ip[:2] + [0, ]
            ip, port = ip[:2]
            ip = Proxy.ip_to_int(ip)
            port = int(port)

            kwargs = dict(
                ip=ip,
                port=port,
            )

            proxy, created = Proxy.objects.get_or_create(**kwargs)

        # статистика по сайтам
        site, created = Site.objects.get_or_create(domain=domain)
        site.save()
        url, created = Url.objects.get_or_create(site=site,
                                                 path=path,
                                                 count=len(ips))
        url.save()

        # поиск ссылок сайта в глубь, если найдены ip-адреса и если глубина не максимальная
        if (len(ips) < self.count_for_deep_scan) and \
                (task.level < self.scan_deep):
            return

        grab.tree.make_links_absolute(grab.response.url)
        links = map(
            lambda item: urlparse(unicode(item)),
            grab.tree.xpath('//a/@href')
        )
        links = filter(
            lambda link: (link.hostname == domain) and
                         not Url.is_exists(*split_url(link.geturl())),
            links
        )
        links = set(map(
            lambda item: item.geturl(),
            links
        ))
        if not links:
            return

        # создание задач на обход ссылок
        for link in links:
            yield task.clone(
                url=link,
                level=task.level + 1,
            )


class Command(BaseCommand):
    help = 'Search proxies'

    def handle(self, *args, **options):
        try:
            finder = ProxyFinder(thread_number=30)
            finder.run()
        except KeyboardInterrupt:
            self.stdout.write('^Interrupt')
