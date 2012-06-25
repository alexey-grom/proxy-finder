# -*- coding: utf-8 -*-

from re import compile, findall
from logging import basicConfig, DEBUG, getLogger

from fetcher import MultiFetcher, Task, Request
from fetcher.utils import url_fix
from fetcher.frontend.sqlalchemy_frontend import create_session

from model import Proxy, Url


logger = getLogger('finder')


_, session = create_session('sqlite:///proxies.sqlite')


class ProxyFinder(MultiFetcher):
    GOOGLE_SEARCH_QUERY = 'http proxy'
    GOOGLE_RESULTS_COUNT = 100
    DEEP = 3
    COUNT_FOR_DEEP_SCAN = 30

    PROXY_MASK = compile('(\d{1,3}[.]\d{1,3}[.]\d{1,3}[.]\d{1,3}[:]\d{1,5})')

    def on_start(self):
        logger.info(u'Открытие гугла.')
        yield Task(
            url='http://google.com',
            handler='google'
        )

    def task_google(self, task, error=None):
        if error or task.response.status_code != 200:
            logger.info(u'Ошибка при открытии гугла - повтор.')
            yield task
            return

        logger.info(u'Отправка запроса.')

        task.get_control('q').value = ProxyFinder.GOOGLE_SEARCH_QUERY

        task.submit(
            submit_name='btnG',
            extra_values=dict(
                num=str(ProxyFinder.GOOGLE_RESULTS_COUNT),
                as_qdr='all',
                sclient='',
                output=''
            )
        )
        yield task.clone(handler='result')

    def task_result(self, task, error=None):
        if error or task.response.status_code != 200:
            logger.info(u'Ошибка при отправке запроса - повтор.')
            yield task
            return

        logger.info(u'Обход поисковых результатов.')

        Request.connection_timeout = 5
        Request.overall_timeout = 10

        for url in task.html.xpath('//h3[@class="r"]/a/@href', all=True):
            logger.info(u'Переход на %s' % url)
            yield task.clone(
                handler='page',
                url=str(url),
                level=0,
                priority=100
            )

    def task_page(self, task, error=None):
        if error or task.response.status_code != 200:
            return

        task.html.make_links_absolute()

        ips = set(
            ip
            for ip in findall(self.PROXY_MASK, task.response.content)
        )

        if not ips:
            logger.info(u'Не найдены ip-адреса на %s!' % task.response.url)

        else:
            logger.info(u'Найдено %d ip-адресов на %s.' % (len(ips), task.response.url))

            for ip in ips:
                Proxy.store_proxy(session, ip)

            if task.level < ProxyFinder.DEEP and len(ips) > ProxyFinder.COUNT_FOR_DEEP_SCAN:
                urls = set(
                    url_fix(unicode(url))
                    for url in task.html.xpath('//a/@href', all=True)
                )
                for url in urls:
                    if not Url.is_exists(session, url):
                        yield Task(
                            handler='page',
                            url=url,
                            level=task.level + 1,
                            priority=task.priority - 1
                        )

            session.commit()


if __name__ == '__main__':
    basicConfig(level=DEBUG)

    proxy_finder = ProxyFinder(
        threads_count=30
    )
    proxy_finder.start()
    proxy_finder.render_stat()

    print u'Найдено %d ip-адресов' % Proxy.count(session)
