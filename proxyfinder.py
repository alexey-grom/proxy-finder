#! /usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright: 2012, Alex Gromov
# Author: Alex Gromov (alexey-grom@jabber.ru)
# License: BSD

from sys import exit
from optparse import OptionParser
import logging

from spiders.finder import ProxyFinder
from spiders.checker import ProxyChecker

from cacher import Cacher


logger = logging.getLogger('proxyfinder')


class Finder(Cacher, ProxyFinder, ProxyChecker):
    ''' Поисковик и чекер прокси '''

    def __init__(self, *args, **kwargs):
        super(Finder, self).__init__(*args, **kwargs)

    def setup_queue(self, backend='mongo', database='proxy_finder', **kwargs):
        super(Finder, self).setup_queue(backend, database, **kwargs)

    def prepare(self):
        '''Подготовка к работе'''

        super(Finder, self).prepare()

    def shutdown(self):
        '''Завершение работы'''

        super(Finder, self).shutdown()

    def finded_proxies(self, proxies):
        '''Сохраняет найденные прокси в mongodb'''

        super(Finder, self).finded_proxies(proxies)

        for proxy in proxies:
            self.save_proxy(proxy)

    def checked_proxy(self, proxy, options):
        '''Вызывается когда прокси успешно проверена'''

        super(Finder, self).checked_proxy(proxy, options)

        self.mark_check_result(proxy, options)

    def is_checked_proxy(self, proxy):
        '''Нужно ли проверять прокси'''

        if self.is_proxy_exists(proxy):
            if not self.is_valid_proxy(proxy):
                return True
            if not self.is_proxy_expired(proxy):
                return True
        else:
            self.save_proxy(proxy)

    def save_proxy(self, proxy):
        '''Сохраняет отдельную прокси и запускает её проверку'''

        if not self.is_checked_proxy(proxy):
            self.mark_check_start(proxy)
            self.check_proxy(proxy)

    def looked_url(self, url):
        '''Проверка необходимости просмотра страницы'''

        if not self.is_url_exists(url):
            self.save_url(url)
            return

        if self.is_url_expired(url):
            self.update_url(url)
            return

        return True


def dump_proxies(get=True, post=True, anonymous=True):
    '''Дампит в stdout прокси с указанными параметрами'''

    cacher = Cacher()

    for proxy in cacher.get_proxy(get, post, anonymous):
        print proxy


def drop_all():
    cacher = Cacher()
    cacher.drop_all()


def main():
    parser = OptionParser(description=u'Поисковик прокси')

    parser.add_option(
        '-t',
        action="store",
        dest='thread_number',
        default=20,
        type='int',
        help=u'количество потоков'
    )

    parser.add_option(
        '-q',
        action="store",
        dest='search_query',
        default='http proxy list',
        help=u'поисковой запрос для гугла'
    )

    parser.add_option(
        '-c',
        action="store",
        dest='search_count',
        default=10,
        type='int',
        help=u'размер выдачи гугла'
    )

    parser.add_option(
        '-f',
        action="store_true",
        dest='fetch_urls',
        default=True,
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

    parser.add_option(
        '-d',
        action="store_true",
        dest='logging',
        default=True,
        help=u'выводить отладочную информацию'
    )

    options, args = parser.parse_args()

    if 'drop' in args:
        drop_all()
    elif 'dump' in args:
        dump_proxies()
    else:
        if options.logging:
            logging.basicConfig(level=logging.DEBUG)

        del options.logging

        proxy_finder = Finder(**vars(options))
        proxy_finder.run()
        proxy_finder.render_stats()

    exit()


if __name__ == '__main__':
    main()
