"""
    Django settings for production
"""

import logging
from pathlib import Path as __Path

from django.utils.translation import gettext_lazy as _


###############################################################################

# Build paths relative to the project root:
BASE_PATH = __Path(__file__).parent.parent.parent
print(f'BASE_PATH:{BASE_PATH}')
assert __Path(BASE_PATH, 'findmydevice_project').is_dir()

###############################################################################
# Find My Device settings
FMD_ACCESS_TOKEN_TIMEOUT_SEC = 5 * 60

# Don't store a new location from Device, if we have one, in this time range:
FMD_MIN_LOCATION_DATE_RANGE_SEC = 30

# Stop trying to find a unique device "short_id" after following rounds.
# Will raise and error and it's need to increase models.device.SHORT_ID_LENGTH
SHORT_ID_MAX_ROUNDS = 100

# The Find My Device has a optional registration token, that must be set by the
# user. If this token is set here, the user must set the same token in the
# Find My Device App to register a new device:
REGISTRATION_TOKEN = 'python'
###############################################################################


# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False

# Serve static/media files by Django?
# In production the Webserver should serve this!
SERVE_FILES = False


# SECURITY WARNING: keep the secret key used in production secret!
__SECRET_FILE = __Path(BASE_PATH, 'secret.txt').resolve()
if not __SECRET_FILE.is_file():
    print(f'Generate {__SECRET_FILE}')
    from secrets import token_urlsafe as __token_urlsafe

    __SECRET_FILE.write_text(__token_urlsafe(128))

SECRET_KEY = __SECRET_FILE.read_text().strip()


# Application definition

INSTALLED_APPS = [
    'bx_django_utils.admin_extra_views.apps.AdminExtraViewsAppConfig',
    'bx_django_utils.admin_extra_views.admin_config.CustomAdminConfig',  # Replaced 'django.contrib.admin'
    #
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    #
    'bx_django_utils',  # https://github.com/boxine/bx_django_utils
    #
    'findmydevice.apps.AppConfig',
]

ROOT_URLCONF = 'findmydevice_project.urls'
APPEND_SLASH = False  # Manually made for /admin/ in urls.py
WSGI_APPLICATION = 'findmydevice_project.wsgi.application'

AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
]
LOGIN_URL = '/admin/login/'

MIDDLEWARE = [
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.middleware.common.CommonMiddleware',
    # TODO: 'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'django.middleware.security.SecurityMiddleware',
]

__TEMPLATE_DIR = __Path(BASE_PATH, 'findmydevice_project', 'templates')
assert __TEMPLATE_DIR.is_dir(), f'Directory not exists: {__TEMPLATE_DIR}'
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        "DIRS": [str(__TEMPLATE_DIR)],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'django.template.context_processors.i18n',
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.template.context_processors.media',
                'django.template.context_processors.csrf',
                'django.template.context_processors.tz',
                'django.template.context_processors.static',
                'findmydevice.context_processors.findmydevice_version_string',
            ],
        },
    },
]


DEFAULT_AUTO_FIELD = 'django.db.models.AutoField'

# _____________________________________________________________________________
# Internationalization

LANGUAGE_CODE = 'en'

LANGUAGES = [
    ('de', _('German')),
    ('en', _('English')),
]
USE_I18N = True
TIME_ZONE = 'Europe/Paris'
USE_TZ = True

# _____________________________________________________________________________
# Static files (CSS, JavaScript, Images)

STATIC_URL = '/static/'  # Can't change! https://gitlab.com/jedie/django-find-my-device/-/issues/7
STATIC_ROOT = str(__Path(BASE_PATH, 'static'))

MEDIA_URL = '/media/'
MEDIA_ROOT = str(__Path(BASE_PATH, 'media'))


# _____________________________________________________________________________
# Cache Backend

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'unique-snowflake',
    }
}


# _____________________________________________________________________________
# cut 'pathname' in log output

old_factory = logging.getLogRecordFactory()


def cut_path(pathname, max_length):
    if len(pathname) <= max_length:
        return pathname
    return f'...{pathname[-(max_length - 3):]}'


def record_factory(*args, **kwargs):
    record = old_factory(*args, **kwargs)
    record.cut_path = cut_path(record.pathname, 30)
    return record


logging.setLogRecordFactory(record_factory)

# -----------------------------------------------------------------------------

LOGGING = {
    'version': 1,
    'disable_existing_loggers': True,
    'formatters': {
        'colored': {  # https://github.com/borntyping/python-colorlog
            '()': 'colorlog.ColoredFormatter',
            'format': '%(log_color)s%(asctime)s %(levelname)8s %(cut_path)s:%(lineno)-3s %(message)s',
        }
    },
    'handlers': {'console': {'class': 'colorlog.StreamHandler', 'formatter': 'colored'}},
    'loggers': {
        '': {'handlers': ['console'], 'level': 'DEBUG', 'propagate': False},
        'django': {'handlers': ['console'], 'level': 'INFO', 'propagate': False},
        'requests': {'handlers': ['console'], 'level': 'DEBUG', 'propagate': False},
        'findmydevice': {'handlers': ['console'], 'level': 'DEBUG', 'propagate': False},
        'findmydevice_project': {'handlers': ['console'], 'level': 'DEBUG', 'propagate': False},
        'fmd_client': {'handlers': ['console'], 'level': 'DEBUG', 'propagate': False},
    },
}
