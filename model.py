# -*- coding: utf-8 -*-

from datetime import datetime

from fetcher.frontend.sqlalchemy_frontend import Model
from sqlalchemy import Column, Integer, String, Boolean, DateTime


class Proxy(Model):
    __tablename__ = 'proxies'

    id = Column(Integer, primary_key=True)

    ip = Column(String(21), index=True, unique=True)
    check_time = Column(DateTime)
    valid = Column(Boolean)

    @classmethod
    def store_proxy(cls, session, ip):
        if not session.query(Proxy).filter_by(ip=ip).first():
            session.add(Proxy(ip=ip))

    @classmethod
    def store_result(cls, session, ip, is_good=True):
        item = session.query(Proxy).filter_by(ip=ip).first()
        item.valid = is_good
        item.check_time = datetime.now()
        session.commit()

    @classmethod
    def count(cls, session):
        return session.query(Proxy).count()

    @classmethod
    def valid_count(cls, session):
        return session.query(Proxy).filter_by(valid=True).count()

    @classmethod
    def iterator(cls, session, count=30):
        table_size = session.query(Proxy).count()

        for offset in xrange(0, table_size, count):
            for proxy in session.query(Proxy).filter_by(check_time=None).offset(offset).limit(count).all():
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
