# -*- coding: utf-8 -*-

from logging import basicConfig, DEBUG, getLogger

from fetcher import MultiFetcher, Task, Request
from fetcher.utils import url_fix
from fetcher.frontend.sqlalchemy_frontend import create_session

from model import Proxy, Url


logger = getLogger('checker')


_, session = create_session('sqlite:///proxies.sqlite')


class ProxyChecker(MultiFetcher):
    IP_RESOLVER = 'http://www.whatsmyip.us/'

    def on_start(self):
        yield Task(
            url=ProxyChecker.IP_RESOLVER,
            handler='local'
        )

    def database_iterator(self):
        Request.connection_timeout = 5
        Request.overall_timeout = 10

        for proxy in Proxy.iterator(session):
            yield Task(
                url=ProxyChecker.IP_RESOLVER,
                handler='resolver',
                proxy=str(proxy.ip)
            )

    def task_local(self, task, error=None):
        if error or task.response.status_code != 200:
            yield task
            return

        self.local_ip = self.extract_ip(task)
        logger.info(u'Текущий IP-адрес: %s' % self.local_ip)

        self.restart_tasks_generator(self.database_iterator())

    def task_resolver(self, task, error=None):
        is_good = True
        if error or task.response.status_code != 200:
            is_good = False

        if is_good:
            ip = self.extract_ip(task)
            if not ip:
                is_good = False
            else:
                is_good = self.local_ip != ip

        logger.info(
            u'%-3s  %s' % (
                'OK' if is_good else 'BAD',
                task.request.proxy
            )
        )

        Proxy.store_result(session, task.request.proxy, is_good)

    def extract_ip(self, task):
        try:
            content = task.response.raw_content
            content = content.split('</textarea>')[0].\
                              split('<textarea')[1].\
                              split('>')[1].\
                              strip()
            return content
        except:
            return


if __name__ == '__main__':
    basicConfig(level=DEBUG)

    proxy_checker = ProxyChecker(
        threads_count=80
    )
    proxy_checker.start()
    proxy_checker.render_stat()

    print u'Рабочих прокси: %d' % Proxy.valid_count(session)