# coding: utf-8

from logging import getLogger

from sqlalchemy import create_engine
from sqlalchemy import (Column,
                        Integer, SmallInteger, String, TIMESTAMP,
                        text,
                        ForeignKey)
from sqlalchemy.dialects.mysql import INTEGER
from sqlalchemy.sql.expression import exists
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


class Site(Base):
    __tablename__ = 'sites'

    id = Column(Integer, primary_key=True)
    domain = Column(String(256))
    #urls

    @staticmethod
    def get_or_create(domain):
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
    def get_or_create(domain, path, **kwargs):
        url = session.query(Url).join(Site).\
            filter(Site.domain == domain, Url.path == path).\
            first()
        if not url:
            url = Url(path=path, **kwargs)
            domain = Site.get_or_create(domain)
            domain.urls.append(url)
            session.merge(domain)
        return url

    @staticmethod
    def is_exists(domain, path):
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
    create_session('root', '654321', echo=False)

    domain = 'google.com'
    urls = [
        '/sfsfsf',
        '/sfsfsf',
        '/sfsfsf2',
        '/sfsfsf3',
        '/sfsfsf4',
    ]

    ip_to_int = lambda ip: reduce(lambda accumulate, x: accumulate * 256 + x, map(int, ip.split('.')))
    ips = [
        ('1.1.1.1', [80, 22]),
        ('1.1.2.1', [80, 22]),
        ('1.1.2.1', [8080, 2222, 80]),
        ('1.1.3.1', [80, 22]),
    ]

    print Site.get_or_create(domain)
    for url in urls:
        print Url.get_or_create(domain, url)

    for ip, ports in ips:
        ip = ip_to_int(ip)
        print Host.get_or_create(ip)
        for port in ports:
            print Port.get_or_create(ip, port)

    session.commit()
