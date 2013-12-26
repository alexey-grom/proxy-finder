# encoding: utf-8

from logging import basicConfig, DEBUG
from re import MULTILINE, findall

from django.core.management.base import BaseCommand, CommandError
from django.utils.translation import ugettext_lazy as _
from grab import Grab
from grab.spider import Spider, Task
from grab.tools.google import build_search_url

from ...models import Proxy, Site, Url
from settings import get_settings


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


class Command(BaseCommand):
    help = _('Search proxies')

    def handle(self, *args, **options):
        basicConfig(level=DEBUG)
        finder = ProxyFinder(thread_number=30)
        try:
            finder.run()
        except KeyboardInterrupt:
            self.stdout.write('^Interrupt\n')
        self.stdout.write(finder.render_stats())
