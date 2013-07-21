# coding: utf-8

from re import MULTILINE
from logging import basicConfig, DEBUG, getLogger
from urlparse import urlparse, urlsplit
from pprint import pprint

from grab import Grab
from grab.spider import Spider, Task
from grab.tools.google import build_search_url
from furl import furl

from model import (create_session, commit_session,
                   Site, Url, Host, Port)


logger = getLogger('finder')


ip_to_int = lambda ip: reduce(lambda accumulate, x: accumulate * 256 + x, map(int, ip.split('.')))


class ProxyFinder(Spider):
    google_search_query = 'free http proxy list'
    google_results_count = 10
    DEEP = 3
    count_for_deep_scan = 10

    ignore_ips = [
        ['10.0.0.0', '10.255.255.255'],
        ['172.16.0.0', '172.31.255.255'],
        ['192.168.0.0 ', '192.168.255.255'],
    ]

    def __init__(self,
                 *args, **kwargs):
        #
        for index, ips_range in enumerate(self.ignore_ips):
            self.ignore_ips[index] = map(ip_to_int, ips_range)

        #
        super(ProxyFinder, self).__init__(*args, **kwargs)
        self.setup_queue()

        #
        grab = Grab()
        grab.setup(
            url=build_search_url(
                self.google_search_query,
                per_page=self.google_results_count,
            ),
            user_agent='Mozilla/4.0 (compatible; MSIE 6.01; Windows NT 6.0)',
        )
        self.add_task(Task(
            'search_result',
            grab=grab
        ))

    def task_search_result(self, grab, task):
        self.process_links(
            grab=grab,
            task_name='page',
            xpath='//li[@class="g"]/h3/a/@href',
            depp_level=0
        )

    def is_ignored_ip(self, ip):
        ip = ip_to_int(ip)
        for range_start, range_end in self.ignore_ips:
            if range_start <= ip or ip <= range_end:
                return True
        return False

    def task_page(self, grab, task):
        url = furl(grab.response.url)

        # поиск ip-адресов
        ips = []
        try:
            ips = grab.doc.rex('(\d{1,3}[.]\d{1,3}[.]\d{1,3}[.]\d{1,3}([:]\d{1,5})?)', flags=MULTILINE).items
            ips = map(
                lambda address: address.group(0).split(':'),
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
            ip = ip[:2]
            ip[0] = ip_to_int(ip[0])
            if len(ip) > 1:
                Port.get_or_create(ip[0], int(ip[1]))
            else:
                Host.get_or_create(ip[0])

        # статистика по сайтам
        Url.get_or_create(url.hostname, url.path, found_count=len(ips))
        commit_session()

        # обход ссылок сайта в глубь, если найдены ip-адреса
        if len(ips) < self.count_for_deep_scan:
            return

        grab.tree.make_links_absolute(grab.response.url)
        links = map(
            lambda item: urlparse(unicode(item)),
            grab.tree.xpath('//a/@href')
        )
        links = filter(
            lambda link: (link.hostname == url.hostname) and not Url.is_exists(link.hostname, link.path),
            links
        )
        links = set(map(
            lambda item: item.path,
            links
        ))
        if not links:
            return

        #pprint(links)

        for link in links:
            #is_exists = Url.is_exists(url.hostname, link)
            #if is_exists:
            #    continue
            yield task.clone(
                url=urlsplit(url.geturl(), link).geturl(),
                level=task.level + 1 if hasattr(task, 'level') else 1,
            )


if __name__ == '__main__':
    basicConfig(level=DEBUG)

    create_session('root', '654321', echo=False)

    proxy_finder = ProxyFinder(
        thread_number=1,
        debug_error=False,
    )
    proxy_finder.run()
