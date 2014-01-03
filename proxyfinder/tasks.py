from celery.task import periodic_task
from celery.schedules import crontab


@periodic_task(run_every=crontab(hour='*/6'), ignore_result=True)
def search():
    from core import ProxyFinder
    finder = ProxyFinder()
    finder.run()


@periodic_task(run_every=crontab(hour='*/1'), ignore_result=True)
def check():
    from core import DBProxyChecker
    checker = DBProxyChecker()
    checker.run()
