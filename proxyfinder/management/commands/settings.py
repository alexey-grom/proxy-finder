from warnings import warn

from django.conf import settings as django_settings


DEFAULT_SETTINGS = {
    'SEARCH': {
        'GOOGLE_QUERIES': [
            'free proxy list',
            'http proxies',
        ],
        'GOOGLE_RESULTS_COUNT': 100,
        'SCAN_DEPTH': 3,
        'COUNT_FOR_DIPPING': 3,
        'IGNORE_IPS': [
            ['10.0.0.0', '10.255.255.255'],
            ['172.16.0.0', '172.31.255.255'],
            ['192.168.0.0 ', '192.168.255.255'],
        ],
    },
    'CHECK': {
        'PORTS': [80, 8080, 8081, 8181, 3128, 808, 8000, ],
        'ITERATE_SIZE': 20,
        'NETWORK_TIMEOUT': 5,
    }
}


class DotDict(dict):
    def __getattr__(self, item):
        if item not in self:
            raise Exception('Setting `%s` is not present!' % item)
        return self[item]


def get_settings():
    if not hasattr(django_settings, 'PROXY_FINDER'):
        warn('Working with default settings for proxy finder!')

    settings = DEFAULT_SETTINGS
    settings.update(getattr(
        django_settings,
        'PROXY_FINDER',
        {}
    ))

    return DotDict(settings)
