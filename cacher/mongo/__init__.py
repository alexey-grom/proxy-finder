# -*- coding: utf-8 -*-

from datetime import datetime

from model import connection


class Cacher(object):
    ''' Слой для хранения прокси и просмотренных URL '''

    def __init__(self, **kwargs):
        self.proxies = connection.proxyfinder.proxies
        self.urls = connection.proxyfinder.urls

    def is_proxy_exists(self, proxy):
        ''' Проверяет есть ли прокси в списке проверенных '''

        item = self.proxies.Proxy()
        item.ip = proxy
        return self.proxies.Proxy.find_one(item)

    def is_valid_proxy(self, proxy):
        '''
        Проверяет валидна ли прокси

        Если проверка уже запускалась, но пометка
        о валидности не поставлена - прокси невалидна
        '''

        # TODO: валидность пожно проверять как any(item.options.values())
        # что означает что какой-то из параметров рабочий, но тогда нужно
        # занулять все параметры перед работой. Благодаря такой проверке
        # можно выкинуть item.valid из модели

        item = self.is_proxy_exists(proxy)
        return item.was_check and item.valid

    def is_proxy_expired(self, proxy, expired_time=60*60):
        ''' Проверяет просрочена ли прокси '''

        item = self.is_proxy_exists(proxy)
        if self.seconds_between(item.check_time) >= expired_time:
            return True

    def save_proxy(self, proxy):
        ''' Сохраняет прокси '''

        item = self.proxies.Proxy()
        item.ip = proxy
        item.save()

    def mark_check_start(self, proxy):
        '''
        Помечает начало проверки прокси

        См. TODO's :62, :30
        '''

        item = self.is_proxy_exists(proxy)
        item.was_check = True
        item.valid = False
        # TODO: возможно требуется очищать options
        # т.к. иначе после перепроверки они не изменятся
        item.save()

    def mark_check_result(self, proxy, options):
        ''' Сохраняет результаты проверки и помечает прокси как проверенную '''

        item = self.is_proxy_exists(proxy)
        item.valid = True
        item.check_time = datetime.now()
        for key, value in options.items():
            item.options[key] = value
        item.save()

    def is_url_exists(self, url):
        '''Проверяет есть ли URL в списке проверенных'''

        item = self.urls.URL()
        item.url = url
        return self.urls.URL.find_one(item)

    def is_url_expired(self, url, expired_time=60*60):
        ''' Проверяет просрочен ли URL '''

        item = self.is_url_exists(url)
        if self.seconds_between(item.check_time) >= expired_time:
            return True

    def save_url(self, url):
        ''' Сохраняет URL в список проверенных '''

        item = self.urls.URL()
        item.url = url
        item.check_time = datetime.now()
        item.save()

    def update_url(self, url):
        ''' Обновляет URL '''

        item = self.is_url_exists(url)
        item.check_time = datetime.now()
        item.save()

    def seconds_between(self, date1, date2=datetime.now()):
        ''' Разница в секундах между двумя датами '''

        elapsed = date2 - date1
        elapsed = elapsed.days * 60 * 60 * 24 + elapsed.seconds
        return elapsed

    def drop_all(self):
        ''' Удаление всей базы '''

        self.proxies.drop()
        self.urls.drop()

    def get_proxies(self, get=True, post=True, anonymous=True):
        ''' Генератор всех прокси по заданным требованиями '''

        item = self.proxies.Proxy()
        item.valid = True
        if get:
            item.get = True
        if post:
            item.post = True
        if anonymous:
            item.anonymous = True

        for proxy in self.proxies.Proxy.find(item):
            yield proxy.ip
