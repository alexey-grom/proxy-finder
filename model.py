# -*- coding: utf-8 -*-

import datetime

from fetcher.frontend.sqlalchemy_frontend import Model
from sqlalchemy import Column, Integer, String, Boolean, DateTime


class Proxy(Model):
    __tablename__ = 'proxies'

    id = Column(Integer, primary_key=True)

    ip = Column(String(21), index=True, unique=True)

    add_time = Column(DateTime)
    check_time = Column(DateTime)

    valid = Column(Boolean)

    is_get = Column(Boolean)
    is_post = Column(Boolean)
    is_anonymous = Column(Boolean)

    def __init__(self, *args, **kwargs):
        self.add_time = datetime.datetime.now()
        super(Proxy, self).__init__(*args, **kwargs)

    @classmethod
    def store_proxy(cls, session, ip):
        if not session.query(Proxy).filter_by(ip=ip).first():
            session.add(Proxy(ip=ip))

    @classmethod
    def count(cls, session):
        return session.query(Proxy).count()

    @classmethod
    def iterator(cls, session, count=30):
        for proxy in session.query(Proxy).yield_per(count):
            yield proxy


class Url(Model):
    __tablename__ = 'urls'

    id = Column(Integer, primary_key=True)
    url = Column(String(255), index=True, unique=True)

    @classmethod
    def is_exists(cls, session, url):
        if not session.query(Url).filter_by(url=url).first():
            session.add(Url(url=url))
            return False
        return True

    @classmethod
    def delete_all(cls, session):
        session.query(Url).delete()
