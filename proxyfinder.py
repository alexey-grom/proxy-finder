#! /usr/bin/env python
# -*- coding: utf-8 -*-

import sys
from optparse import OptionParser

from spider import ProxyFinder


class Finder(ProxyFinder):
    '''
    Наследник поисковика с перегруженным методом
    сохранения найденных прокси
    '''

    def save_proxies(self, proxies):
        '''
        Сохраняет найденные прокси в *А КУДА?*
        '''

        # TODO: и где епта?


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
        default='free proxy',
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

    proxy_finder = Finder(**vars(options))
    proxy_finder.run()
    proxy_finder.render_stats()

    sys.exit()


if __name__ == '__main__':
    main()
