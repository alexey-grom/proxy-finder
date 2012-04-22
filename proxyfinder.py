#! /usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import datetime
from optparse import OptionParser
import logging

import pymongo

from spiders.finder import ProxyFinder
from spiders.checker import ProxyChecker


logger = logging.getLogger('proxyfinder')


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
        self.proxies = self.database['proxies']
        self.urls = self.database['urls']

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
            self.save_proxy(proxy, from_url)

    def checked_proxy(self, proxy, options):
        '''
        Вызывается когда прокси успешно проверена
        '''

        item = dict(
            address=proxy,
        )

        additional = dict(
            check_time=datetime.datetime.now()
        )

        options.update(additional)

        self.proxies.update(item, {'$set': options})

        logger.debug(u'Проверена прокси %s' % proxy)

    def save_proxy(self, proxy, from_url=None):
        '''
        Сохраняет отдельную прокси и запускает её проверку
        '''

        # формируем словарь, по которому будем искать прокси в БД

        item = dict(
            address=proxy,
        )

        # добавляем прокси если её нет в БД

        if not self.proxies.find(item).count():
            additional = dict(
                checked=False,
                added=datetime.datetime.now(),
                from_url=from_url
            )

            item.update(additional)

            self.proxies.save(item)

        # ищем прокси и если она проверялась слишком давно или не проверялась
        # вообще - запускаем проверку

        item = self.proxies.find_one(item)

        now = datetime.datetime.now()
        check_elapsed = now - item.get('check_time', now)
        check_elapsed = check_elapsed.total_seconds()

        if not item.get('checked', False) or check_elapsed > 60*60:
            self.check_proxy(proxy)


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

    #logging.basicConfig(level=logging.DEBUG)

    proxy_finder = Finder(**vars(options))
    proxy_finder.run()
    proxy_finder.render_stats()

    sys.exit()


if __name__ == '__main__':
    main()
