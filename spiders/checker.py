#! /usr/bin/env python
# -*- coding: utf-8 -*-

import logging

from grab.spider import Spider, Task


logger = logging.getLogger('proxyfinder.checker')


GREATEST_PRIORITY = 1


class ProxyChecker(Spider):
    '''
    Чекер прокси
    '''

    def __init__(self,
                 check_try_count=1, check_timeout=5,
                 *args, **kwargs):
        '''
        :param check_try_count: Количество попыток подключения
        :param check_timeout: Таймаут для попытки подключения
        '''

        super(ProxyChecker, self).__init__(
            network_try_limit=check_try_count,
            task_try_limit=check_try_count,
            *args, **kwargs
        )

        self.check_timeout = check_timeout

    def prepare(self):
        '''
        Подготовка к работе
        '''

        super(ProxyChecker, self).prepare()

        # Запрос внешнего ip-адреса

        logger.debug(u'Запрос внешнего ip-адреса')

        task = Task(name='get_ip',
                    url='http://www.whatsmyip.us/',
                    priority=GREATEST_PRIORITY)

        self.add_task(task)

        # Данные для проверки POST-запроса

        self.post_check_data = dict(
            some_string='string_value',
            some_int=154
        )

    def task_get_ip(self, grab, task):
        '''
        Получен внешний ip-адрес
        '''

        ip_address = grab.xpath('id("do")/text()')

        if not ip_address:
            logger.debug(u'Неудалось получить внешний ip-адрес')
            return

        ip_address = ip_address.strip()

        logger.debug(u'Внешний ip-адрес найден: %s' % ip_address)

        self.ip_address = ip_address


    def check_proxy(self, proxy):
        '''
        Добавляет задачу для проверки прокси
        '''

        logger.debug(u'Проверка прокси %s' % proxy)

        # Запросы которые нужно проверить для прокси

        requests = dict(
            GET=dict(
                url='http://www.whatsmyip.us/',
            ),
            POST=dict(
                url='http://www.posttestserver.com/',
                post=self.post_check_data
            )
        )

        # Инициация запросов для прокси

        for name, params in requests.items():
            grab = self.create_grab_instance()

            grab.setup(proxy=proxy,
                       proxy_type='http',
                       connect_timeout=self.check_timeout,
                       timeout=self.check_timeout * 2,
                       **params)

            task = Task(
                name='check_%s' % (name.lower()),
                grab=grab,
                disable_cache=True,
                proxy=proxy,
            )

            self.add_task(task)

    def task_check_get(self, grab, task):
        '''
        Проверен GET-запрос
        '''

        if grab.response.code != 200:
            return

        ip_address = grab.xpath('id("do")/text()')

        if not ip_address:
            return

        ip_address = ip_address.strip()

        options = dict(
            checked=True,
            anonymous=ip_address != self.ip_address,
            get=True,
        )

        self.checked_proxy(task.proxy, options)

    def task_check_post(self, grab, task):
        '''
        Проверен POST-запрос
        '''

        if grab.response.code != 200:
            return

        options = dict(
            checked=True,
            post=True,
        )

        self.checked_proxy(task.proxy, options)

    def checked_proxy(self, proxy, options):
        '''
        Вызывается когда прокси успешно проверена

        :param proxy: Проверенная прокси
        :param options: Параметры прокси
        '''

        logger.debug(
            u'Прокси %s проверена. Результат: %s' % (proxy, options)
        )
