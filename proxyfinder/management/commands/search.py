# encoding: utf-8

from logging import basicConfig, DEBUG

from django.core.management.base import BaseCommand, CommandError
from django.utils.translation import ugettext_lazy as _

from ...core import ProxyFinder


class Command(BaseCommand):
    help = _('Search proxies')

    def handle(self, *args, **options):
        basicConfig(level=DEBUG)
        finder = ProxyFinder()
        try:
            finder.run()
        except KeyboardInterrupt:
            self.stdout.write('^Interrupt\n')
        self.stdout.write(finder.render_stats())
