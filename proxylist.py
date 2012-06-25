# -*- coding: utf-8 -*-

from fetcher.frontend.sqlalchemy_frontend import create_session

from model import Proxy, Url


_, session = create_session('sqlite:///proxies.sqlite')


if __name__ == '__main__':
    for proxy in Proxy.valid_iterator(session):
        print proxy.ip
