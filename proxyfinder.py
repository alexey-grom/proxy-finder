#! /usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import re
from optparse import OptionParser
import logging

from grab.spider import Spider, Task
from grab.tools.rex import rex_text_list


PROXY_MASK = re.compile('(\d{1,3}[.]\d{1,3}[.]\d{1,3}[.]\d{1,3}([:]\d{1,5})?)')


class ProxyFinder(Spider):
    initial_urls = ['http://google.com']

    def __init__(self,
                 search_query='free proxy', search_count=100,
                 fetch_urls=False, fetch_level=2,
                 *args, **kwargs):
        '''
        :param search_query: Поисковой запрос для гугла
        :param search_count: Максимальное количество резальтатов в выдаче гугла
        :param fetch_urls: Если True - кроме основной страницы сайта
            будет загружать остальные на глубину fetch_level
        :param fetch_level: Глубина просмотра сайтов.
            fetch_level=1 - это только заглавная страница
            fetch_level=2 - заглавная страница + просмотр все url с нее. И т.д.
        '''

        super(ProxyFinder, self).__init__(*args, **kwargs)

        self.search_query = search_query
        self.search_count = search_count
        self.fetch_urls = fetch_urls
        self.fetch_level = fetch_level

    def task_initial(self, grab, task):
        '''
        Инициирует поисковой запрос к гуглу
        '''

        # если не перезаписывать некоторые параметры в post -
        # то параметр num (количество поисковых результатов) перестает работать

        post = dict(
            q = self.search_query,
            num = self.search_count,
            as_qdr = 'all',
            sclient = '',
            output = '',
        )

        grab.submit(make_request=False,
                    extra_post=post)

        yield Task(name='search',
                   grab=grab)

    def task_search(self, grab, task):
        '''
        Вызывается когда получен результат поискового запроса
        '''

        # выборка всех ссылок

        urls = grab.xpath_list('//h3[@class="r"]/a/@href')

        for url in urls:
            print url
            # url может быть относительным, поэтому нужно скопировать grab
            g = grab.clone()
            grab.setup(url=url)
            #
            yield Task(
                name='list',
                grab=g,
                level=self.fetch_level - 1
            )

    def task_list(self, grab, task):
        '''
        Вызывается когда получена очередная страница сайта
        '''

        # поиск всех ip[:port] на странице

        proxies = rex_text_list(grab.response.unicode_body(), PROXY_MASK)
        print len(proxies)

        # если требуется просматривать сайт - выборка всех ссылок
        # и инициация заданий

        if not self.fetch_urls or not task.level:
            return

        urls = grab.xpath_list('//a/@href')

        for url in urls:
            #
            g = grab.clone()
            g.setup(url=url)
            #
            yield Task(
                name='list',
                grab=g,
                level=task.level - 1
            )


def main():
    parser = OptionParser(description=u'Поисковик прокси')

    parser.add_option('-t',
        action="store",
        dest='threads_count',
        default=10,
        help=u'количество потоков')

    parser.add_option('-q',
        action="store",
        dest='search_query',
        default='free proxy',
        help=u'поисковой запрос для гугла')

    parser.add_option('-c',
        action="store",
        dest='search_count',
        default=100,
        help=u'размер выдачи гугла')

    parser.add_option('-f',
        action="store_true",
        dest='fetch_urls',
        help=u'сканировать сайты')

    parser.add_option('-l',
        action="store",
        dest='fetch_level',
        default=2,
        help=u'глубина сканирования сайтов')

    options, _ = parser.parse_args()

    proxy_finder = ProxyFinder(
        search_query=options.search_query,
        search_count=options.search_count,
        fetch_urls=options.fetch_urls,
        fetch_level=options.fetch_level,
        thread_number=options.threads_count,
    )
    proxy_finder.run()
    proxy_finder.render_stats()

    sys.exit()


if __name__ == '__main__':
    main()
