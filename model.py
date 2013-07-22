# coding: utf-8

from logging import getLogger
from urlparse import urlparse

from sqlalchemy import create_engine
from sqlalchemy import (Column,
                        Integer, SmallInteger, String, TIMESTAMP,
                        text,
                        ForeignKey)
from sqlalchemy.dialects.mysql import INTEGER
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import relationship, backref


logger = getLogger('storage')


Base = declarative_base()
Session = sessionmaker()
session = None


def create_session(user, password,
                   database='proxy_finder',
                   host='localhost', port=3306,
                   engine='mysql',
                   echo=False):
    global session
    engine = create_engine(
        '%(engine)s://%(user)s:%(password)s@%(host)s:%(port)d/%(database)s?charset=utf8' % dict(
            user=user,
            password=password,
            database=database,
            host=host,
            port=port,
            engine=engine
        ),
        echo=echo
    )
    Base.metadata.create_all(engine)
    Session.configure(bind=engine)
    session = Session()


def commit_session():
    session.commit()


def split_url(url):
    domain = urlparse(url).hostname
    path = domain.join(url.split(domain)[1:])
    return domain, path


class Site(Base):
    __tablename__ = 'sites'

    id = Column(Integer, primary_key=True)
    domain = Column(String(256))
    #urls

    @staticmethod
    def get_or_create(url):
        domain, path = split_url(url)

        result = session.query(Site).\
            filter_by(domain=domain).\
            first()
        if not result:
            result = Site(domain=domain)
            session.add(result)
        return result


class Url(Base):
    __tablename__ = 'urls'

    id = Column(Integer, primary_key=True)
    domain_id = Column(Integer, ForeignKey('sites.id'), nullable=False)
    domain = relationship('Site', backref=backref('urls'))
    path = Column(String(1024))
    found_count = Column(Integer, default=0)
    check_date = Column(TIMESTAMP, server_default=text('CURRENT_TIMESTAMP'), server_onupdate=text('CURRENT_TIMESTAMP'))

    @staticmethod
    def get_or_create(url, **kwargs):
        domain, path = split_url(url)
        print domain, path

        result = session.query(Url).join(Site).\
            filter(Site.domain == domain, Url.path == path).\
            first()
        if not result:
            result = Url(path=path, **kwargs)
            domain = Site.get_or_create(url)
            domain.urls.append(result)
            session.merge(domain)
        return result

    @staticmethod
    def is_exists(url):
        domain, path = split_url(url)

        # TODO: refactor for exists
        result = session.query(Url).join(Site).\
            filter(Site.domain == domain, Url.path == path).\
            first()
        return result is not None


class Host(Base):
    __tablename__ = 'hosts'

    id = Column(Integer, primary_key=True)
    ip = Column(INTEGER(unsigned=True), unique=True)
    #ports

    @staticmethod
    def get_or_create(ip):
        if not isinstance(ip, int):
            raise TypeError()
        result = session.query(Host).\
            filter_by(ip=ip).\
            first()
        if not result:
            result = Host(ip=ip)
            session.add(result)
        return result

    def __repr__(self):
        return '<Host %s>' % self.ip


class Port(Base):
    __tablename__ = 'ports'

    id = Column(Integer, primary_key=True)
    ip_id = Column(Integer, ForeignKey('hosts.id'), nullable=False)
    ip = relationship('Host', backref=backref('ports'))
    port = Column(SmallInteger, nullable=False)
    check_date = Column(TIMESTAMP, server_onupdate=text('CURRENT_TIMESTAMP'))

    @staticmethod
    def get_or_create(ip, port):
        if not isinstance(ip, int) or not isinstance(port, int):
            raise TypeError()
        result = session.query(Port).join(Host).\
            filter(Host.ip == ip, Port.port == port).\
            first()
        if not result:
            result = Port(port=port)
            host = Host.get_or_create(ip)
            host.ports.append(result)
            session.merge(host)
        return result

    def __repr__(self):
        return '<Port %s:%s>' % (self.ip, self.port)


if __name__ == '__main__':
    pass
