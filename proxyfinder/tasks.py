# encoding: utf-8

from os.path import join
from fcntl import flock, LOCK_EX, LOCK_NB
from datetime import timedelta, datetime
from hashlib import md5

from celery import current_task
from celery.task import PeriodicTask
from celery.result import AsyncResult
from celery.schedules import crontab


class TaskLock(object):
    def __init__(self, filename):
        self.file = open(filename, 'w+')
        self._previous_task_id = None

    @property
    def previous_task_id(self):
        return self._previous_task_id

    def __enter__(self):
        try:
            flock(self.file.fileno(), LOCK_EX | LOCK_NB)

            self._previous_task_id = self.file.read()
            self.file.seek(0)
            self.file.write(current_task.request.id)
            self.file.truncate()

            return True

        except IOError:
            pass

        return False

    def __exit__(self, *args):
        self.file.close()


class SinglePeriodicTask(PeriodicTask):
    abstract = True
    run_every = crontab(minute='*/1')
    ignore_result = False

    def __init__(self):
        if not hasattr(self, 'restart_delay'):
            raise NotImplementedError('Single periodic tasks '
                                      'must have a restart_delay attribute')
        super(SinglePeriodicTask, self).__init__()

    def __call__(self, *args, **kwargs):
        lock_filename = join('/tmp',
                             md5(self.name).hexdigest() + '.lock')
        lock = TaskLock(lock_filename)
        with lock as is_locked:
            if not is_locked:
                return

            previous_task = AsyncResult(lock.previous_task_id)
            if previous_task.result and datetime.now() - previous_task.result < self.restart_delay:
                return previous_task.result

            super(SinglePeriodicTask, self).__call__(*args, **kwargs)

            return datetime.now()


class SearchTask(SinglePeriodicTask):
    restart_delay = timedelta(hours=4)

    def run(self, *args, **kwargs):
        from core import ProxyFinder
        finder = ProxyFinder()
        try:
            finder.run()
        except KeyboardInterrupt:
            pass


class CheckTask(SinglePeriodicTask):
    restart_delay = timedelta(hours=4)

    def run(self, *args, **kwargs):
        from core import DBProxyChecker
        checker = DBProxyChecker()
        try:
            checker.run()
        except KeyboardInterrupt:
            pass
