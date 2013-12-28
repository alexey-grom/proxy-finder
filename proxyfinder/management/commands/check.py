# encoding: utf-8

from django.core.management.base import BaseCommand, CommandError
from django.utils.translation import ugettext_lazy as _

from ...core import DBProxyChecker


class Command(BaseCommand):
    help = _('Search proxies')

    def handle(self, *args, **options):
        try:
            checker = DBProxyChecker()
            checker.run()
        except KeyboardInterrupt:
            self.stdout.write('^Interrupt')
