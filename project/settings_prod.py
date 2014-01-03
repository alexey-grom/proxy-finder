from settings import *


ALLOWED_HOSTS = ['*', ]

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'proxy_finder',
        'USER': 'root',
        'PASSWORD': '654321',
    }
}
