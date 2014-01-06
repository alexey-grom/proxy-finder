"""
Django settings for project project.

For more information on this file, see
https://docs.djangoproject.com/en/1.6/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.6/ref/settings/
"""

import os

from django.utils.translation import ugettext_lazy as _


BASE_DIR = os.path.dirname(os.path.dirname(__file__))
relative_path = lambda *args: os.path.join(BASE_DIR, *args)


SITE_ID = 1


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.6/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = '%shvv0!dce3ow#kw9(y&400cs+s+q=_hoban#^eg9p_5+kh*ha'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True
TEMPLATE_DEBUG = DEBUG

INTERNAL_IPS = ['127.0.0.1', ]
ALLOWED_HOSTS = ['*', ]


DEBUG_TOOLBAR_PANELS = [
    'debug_toolbar.panels.versions.VersionsPanel',
    'debug_toolbar.panels.timer.TimerPanel',
    'debug_toolbar.panels.settings.SettingsPanel',
    'debug_toolbar.panels.headers.HeadersPanel',
    'debug_toolbar.panels.request.RequestPanel',
    'debug_toolbar.panels.sql.SQLPanel',
    'debug_toolbar.panels.templates.TemplatesPanel',
    'debug_toolbar.panels.staticfiles.StaticFilesPanel',
    'debug_toolbar.panels.cache.CachePanel',
    'debug_toolbar.panels.signals.SignalsPanel',
    'debug_toolbar.panels.logging.LoggingPanel',
    'debug_toolbar.panels.redirects.RedirectsPanel',
    'debug_toolbar.panels.profiling.ProfilingPanel',
    'debug_toolbar_line_profiler.panel.ProfilingPanel',
]


# Application definition

INSTALLED_APPS = [
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sites',
    'django.contrib.flatpages',

    'grappelli',
    'django.contrib.admin',

    'djcelery',
    'kombu.transport.django',

    'south',
    'debug_toolbar',
    'debug_toolbar_line_profiler',
    'rest_framework',
    'rosetta',
    'pipeline',
    'bootstrap3',
    'django_extensions',

    'layout',
    'proxyfinder',

]

MIDDLEWARE_CLASSES = [
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.cache.CacheMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'pipeline.middleware.MinifyHTMLMiddleware',
    'django.middleware.gzip.GZipMiddleware',
    'debug_toolbar.middleware.DebugToolbarMiddleware',
]

ROOT_URLCONF = 'project.urls'

WSGI_APPLICATION = 'project.wsgi.application'


# Database
# https://docs.djangoproject.com/en/1.6/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'proxy_finder',
        'USER': 'root',
        'PASSWORD': '654321',
    }
}

# Internationalization
# https://docs.djangoproject.com/en/1.6/topics/i18n/

LANGUAGE_CODE = 'ru-ru'
TIME_ZONE = 'Asia/Novosibirsk'

USE_I18N = True
USE_L10N = True
USE_TZ = True

LOCALE_PATHS = (
    os.path.join(BASE_DIR, 'proxyfinder', 'locale'),
)

LANGUAGES = (
    ('en', _('English')),
    ('ru', _('Russian')),
)

ROSETTA_WSGI_AUTO_RELOAD = True
ROSETTA_MESSAGES_PER_PAGE = 100

#
TEMPLATE_CONTEXT_PROCESSORS = [
    'django.contrib.auth.context_processors.auth',
    'django.core.context_processors.debug',
    'django.core.context_processors.i18n',
    'django.core.context_processors.media',
    'django.core.context_processors.static',
    'django.core.context_processors.tz',
    'django.core.context_processors.request',
    'django.contrib.messages.context_processors.messages',
    'django.core.context_processors.i18n',
    'layout.context_processors.current_site',
]


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.6/howto/static-files/

STATIC_URL = '/static/'
STATIC_ROOT = relative_path('static')
STATICFILES_STORAGE = 'pipeline.storage.PipelineCachedStorage'

PIPELINE_ENABLED = not DEBUG
PIPELINE_CSS = {
    'vendor': {
        'source_filenames': (
            'css/bootstrap.css',
        ),
        'output_filename': 'css/vendor.css',
    },
    'own': {
        'source_filenames': (
            'css/main.css',
        ),
        'output_filename': 'css/own.css',
    },
}

PIPELINE_JS = {
    'header': {
        'source_filenames': (
            'js/vendor/jquery-1.10.1.min.js',
            'js/vendor/modernizr-2.6.2-respond-1.1.0.min.js',
        ),
        'output_filename': 'js/header.js',
    },
    'footer': {
        'source_filenames': (
            'js/vendor/bootstrap.js',
            'js/vendor/angular.js',
            'js/main.js',
        ),
        'output_filename': 'js/footer.js',
    }
}

PIPELINE_CSS_COMPRESSOR = 'pipeline.compressors.yuglify.YuglifyCompressor'
PIPELINE_JS_COMPRESSOR = 'pipeline.compressors.yuglify.YuglifyCompressor'


REST_FRAMEWORK = {
    'DEFAULT_RENDERER_CLASSES': (
        'rest_framework.renderers.BrowsableAPIRenderer',
        'rest_framework.renderers.JSONRenderer',
    ),

    # Use hyperlinked styles by default.
    # Only used if the `serializer_class` attribute is not set on a view.
    'DEFAULT_MODEL_SERIALIZER_CLASS': 'rest_framework.serializers.HyperlinkedModelSerializer',

    # Use Django's standard `django.contrib.auth` permissions,
    # or allow read-only access for unauthenticated users.
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.DjangoModelPermissionsOrAnonReadOnly'
    ]
}


# CELERY
import djcelery
djcelery.setup_loader()

BROKER_URL = 'django://'
CELERYBEAT_SCHEDULER = "djcelery.schedulers.DatabaseScheduler"
CELERY_REDIRECT_STDOUTS = False


LOGGING = {
    'version': 1,
    'handlers': {
        'null': {
            'level': 'DEBUG',
            'class': 'logging.NullHandler',
        },
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'propagate': True,
            'level': 'INFO',
        },
        'grab': {
            'handlers': ['console'],
            'level': 'DEBUG',
        },
        'proxy-checker': {
            'handlers': ['console'],
            'level': 'DEBUG',
        }
    }
}


CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
    }
}


from settings_local import *
