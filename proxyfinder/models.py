# encoding: utf-8

from urlparse import urlparse
from datetime import timedelta

from django.db import models
from django.utils.timezone import now
from django.utils.translation import ugettext_lazy as _

from countries import country_codes


class ProxyQualityManager(models.Manager):
    def get_queryset(self):
        queryset = super(ProxyQualityManager, self).get_queryset()
        queryset = queryset.extra(select={
            'quality': 'is_anonymously * 30 + '
                       'is_post * 20 + '
                       'is_get * 10',
        })
        return queryset


class Proxy(models.Model):
    TYPE = [
        'unknown',
        'http',
        'socks4',
        'socks5',
    ]
    TYPE_CHOICES = [(index, _(value))
                    for index, value in enumerate(TYPE)]

    ip = models.PositiveIntegerField(db_index=True,
                                     verbose_name=_('Long IP address'))
    port = models.PositiveSmallIntegerField(db_index=True,
                                            verbose_name=_('Port'))

    type = models.PositiveSmallIntegerField(choices=TYPE_CHOICES,
                                            default=0,
                                            verbose_name=_('Proxy type'))

    is_get = models.BooleanField(db_index=True,
                                 default=False,
                                 verbose_name=_('Can GET'))
    is_post = models.BooleanField(db_index=True,
                                  default=False,
                                  verbose_name=_('Can POST'))
    is_anonymously = models.BooleanField(db_index=True,
                                         default=False,
                                         verbose_name=_('Is anonymously'))

    country_code = models.CharField(db_index=True,
                                    max_length=5,
                                    blank=True,
                                    null=True,
                                    choices=country_codes.items(),
                                    verbose_name=_('Country code'))

    updated = models.DateTimeField(auto_now=True,
                                   auto_now_add=True,
                                   verbose_name=_('Updated at'))

    checked = models.DateTimeField(blank=True,
                                   null=True,
                                   verbose_name=_('Checked at'))

    objects = models.Manager()
    quality = ProxyQualityManager()

    def address(self, port=None):
        u"""Перевод хранящегося в long адреса в строковое представление"""

        global ip
        ip = int(self.ip)

        def mod255():
            global ip
            result = ip % 256
            ip = ip / 256
            return result

        parts = [
            str(mod255())
            for _ in range(4)
        ]
        address = '.'.join(reversed(parts))

        if port:
            address += ':' + str(port)

        return address

    def format(self):
        return self.address(self.port)

    def type_name(self):
        return self.TYPE[self.type]

    def country(self):
        if self.country_code not in country_codes:
            return _('unknown')
        return country_codes[self.country_code]

    def __unicode__(self):
        info = [self.address(self.port),
                self.TYPE[self.type]]
        if self.is_get:
            info.append('GET')
        if self.is_post:
            info.append('POST')
        if self.is_anonymously:
            info.append('anonymously')
        return ' '.join(info)

    def as_tuple(self):
        return (self.address(), self.port)

    @staticmethod
    def ip_to_int(ip):
        u"""Перевод строкового представления ip в long"""
        return reduce(
            lambda accumulate, x: accumulate * 256 + x,
            map(int, ip.split('.'))
        )

    class Meta:
        unique_together = [
            ['ip', 'port', ],
        ]
        ordering = ['-checked', 'ip', 'port', ]
        verbose_name = _('Proxy')
        verbose_name_plural = _('Proxies')


class Site(models.Model):
    domain = models.CharField(max_length=255,
                              unique=True,
                              db_index=True,
                              verbose_name=_('Domain'))

    def __unicode__(self):
        return self.domain

    class Meta:
        verbose_name = _('Site')
        verbose_name_plural = _('Sites')


class Url(models.Model):
    site = models.ForeignKey('Site',
                             verbose_name=_('Site'))
    path = models.CharField(max_length=1024 * 4,
                            verbose_name=_('Path'))

    checked = models.DateTimeField(auto_now_add=True,
                                   auto_now=True,
                                   verbose_name=_('Last check time'))
    count = models.SmallIntegerField(verbose_name=_('Finded count'),
                                     blank=True,
                                     null=True,
                                     default=None)

    @staticmethod
    def split_url(url):
        parse = urlparse(url)
        if not parse.scheme.startswith('http'):
            return None, None
        domain = parse.hostname
        path = domain.join(url.split(domain)[1:])
        return domain, path

    @staticmethod
    def is_exists(url):
        domain, path = Url.split_url(url)
        return Url.objects.\
            filter(site__domain=domain,
                   path=path,
                   checked__lt=now() - timedelta(hours=1)).\
            exists()

    class Meta:
        verbose_name = _('Url')
        verbose_name_plural = _('Urls')
