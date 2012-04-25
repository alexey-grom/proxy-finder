import datetime

import mongokit


connection = mongokit.Connection()


@connection.register
class Proxy(mongokit.Document):
    structure = {
        'ip': str,
        'was_check': bool,
        'valid': bool,
        'options': {
            'get': bool,
            'post': bool,
            'anonymous': bool,
        },
        'add_time': datetime.datetime,
        'check_time': datetime.datetime,
    }
    required_fields = ['ip']
    default_values = {
        'add_time': datetime.datetime.now,
        'was_check': False,
        'valid': False,
    }
    use_dot_notation=True


@connection.register
class URL(mongokit.Document):
    structure = {
        'url': unicode,
        'add_time': datetime.datetime,
        'check_time': datetime.datetime,
    }
    required_fields = ['url']
    default_values = {
        'add_time': datetime.datetime.now,
    }
    use_dot_notation=True


proxies = connection.proxyfinder.proxies
urls = connection.proxyfinder.urls
