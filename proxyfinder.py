#! /usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import datetime
from optparse import OptionParser
import logging

import pymongo

from finder import ProxyFinder
from checker import ProxyChecker


class Finder(ProxyFinder, ProxyChecker):
    '''
    Наследник поисковика с перегруженным методом
    сохранения найденных прокси
    '''

    def prepare(self):
        '''
        Подготовка к работе
        '''

        super(Finder, self).prepare()

        connection = pymongo.Connection()
        self.database = connection['proxy-finder']
        self.collection = self.database['proxies']

    def shutdown(self):
        '''
        Завершение работы
        '''

        super(Finder, self).shutdown()

    def finded_proxies(self, proxies, from_url=None):
        '''
        Сохраняет найденные прокси в mongodb
        '''

        super(Finder, self).finded_proxies(proxies, from_url)

        for proxy in proxies:
            #self.save_proxy(proxy)
            self.check_proxy(proxy)

    def save_proxy(self, proxy, from_url=None):
        '''
        Сохраняет отдельную прокси
        '''

        item = dict(
            address=proxy,
        )

        if self.collection.find(item).count():
            return

        additional = dict(
            checked=False,
            added=datetime.datetime.now()
        )

        item.update(additional)

        self.collection.save(item)


def main():
    parser = OptionParser(description=u'Поисковик прокси')

    parser.add_option(
        '-t',
        action="store",
        dest='thread_number',
        default=10,
        type='int',
        help=u'количество потоков'
    )

    parser.add_option(
        '-q',
        action="store",
        dest='search_query',
        default='free http proxy list',
        help=u'поисковой запрос для гугла'
    )

    parser.add_option(
        '-c',
        action="store",
        dest='search_count',
        default=100,
        type='int',
        help=u'размер выдачи гугла'
    )

    parser.add_option(
        '-f',
        action="store_true",
        dest='fetch_urls',
        help=u'сканировать сайты'
    )

    parser.add_option(
        '-l',
        action="store",
        dest='fetch_level',
        default=2,
        type='int',
        help=u'глубина сканирования сайтов'
    )

    options, _ = parser.parse_args()

    logging.basicConfig(level=logging.DEBUG)

    proxy_finder = Finder(**vars(options))
    proxy_finder.run()
    proxy_finder.render_stats()

    sys.exit()


if __name__ == '__main__':
    main()
