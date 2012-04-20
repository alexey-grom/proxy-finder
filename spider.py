#! /usr/bin/env python
# -*- coding: utf-8 -*-

import re
from urlparse import urlparse

from grab.spider import Spider, Task
from grab.tools.rex import rex_text_list


PROXY_MASK = re.compile('(\d{1,3}[.]\d{1,3}[.]\d{1,3}[.]\d{1,3}([:]\d{1,5})?)')


class ProxyFinder(Spider):
    '''
    Поисковик прокси через гугл
    '''

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

        # нормализация и всех ссылок

        grab.tree.make_links_absolute(grab.response.url)

        urls = grab.xpath_list('//h3[@class="r"]/a/@href')

        for url in urls:
            if not self.validate_url(url):
                continue

            yield Task(
                name='list',
                url=url,
                level=self.fetch_level - 1
            )

    def task_list(self, grab, task):
        '''
        Вызывается когда получена очередная страница сайта
        '''

        # поиск всех ip[:port] на странице

        proxies = rex_text_list(grab.response.unicode_body(), PROXY_MASK)
        self.save_proxies(proxies)

        # если требуется просматривать сайт - выборка всех ссылок
        # и инициация заданий

        if not self.fetch_urls or not task.level:
            return

        # нормализация и всех ссылок на странице
        grab.tree.make_links_absolute(grab.response.url)

        urls = grab.xpath_list('//a/@href')

        for url in urls:
            if not self.validate_url(url):
                continue

            yield Task(
                name='list',
                url=url,
                level=task.level - 1
            )

    def validate_url(self, url):
        '''
        Проверка валидности url
        '''

        url = urlparse(url)
        if url.scheme in ['http', 'https']:
            return True

    def save_proxies(self, proxies):
        '''
        Вызывается когда нужно сохранить найденные прокси

        :param proxies: Список найденных прокси
        '''
