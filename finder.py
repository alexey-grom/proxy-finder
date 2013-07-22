# coding: utf-8

from re import MULTILINE
from logging import basicConfig, DEBUG, getLogger
from urlparse import urlparse

from grab import Grab
from grab.spider import Spider, Task
from grab.tools.google import build_search_url

from model import (create_session, commit_session,
                   split_url,
                   Site, Url, Host, Port)


#logger = getLogger('finder') # TODO: добавить логгирование


ip_to_int = lambda ip: reduce(lambda accumulate, x: accumulate * 256 + x, map(int, ip.split('.')))


class ProxyFinder(Spider):
    google_search_query = 'free http proxy list'
    google_results_count = 10
    scan_deep = 3
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
        if not hasattr(task, 'level'):
            task.level = 0

        domain, _ = split_url(grab.response.url)
        #url = urlparse(grab.response.url)

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
        Url.get_or_create(grab.response.url, found_count=len(ips))
        commit_session()

        # поиск ссылок сайта в глубь, если найдены ip-адреса и если глубина не максимальная
        if (len(ips) < self.count_for_deep_scan) and (task.level < self.scan_deep):
            return

        grab.tree.make_links_absolute(grab.response.url)
        links = map(
            lambda item: urlparse(unicode(item)),
            grab.tree.xpath('//a/@href')
        )
        links = filter(
            lambda link: (link.hostname == domain) and not Url.is_exists(link.geturl()),
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


if __name__ == '__main__':
    basicConfig(level=DEBUG)

    create_session('root', '654321', echo=False)

    proxy_finder = ProxyFinder(
        thread_number=1,
        debug_error=False,
    )
    proxy_finder.run()
