# ruff: noqa: F405

"""
    Django settings for local development via Docker
"""

import os as __os
import sys as __sys

from findmydevice_project.settings.prod import *  # noqa


# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

# Required for the debug toolbar to be displayed:
INTERNAL_IPS = ('*',)

ALLOWED_HOSTS = ('*',)

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': __os.environ.get('DB_NAME'),
        'USER': __os.environ.get('DB_USER'),
        'PASSWORD': __os.environ.get('DB_PASS'),
        'HOST': __os.environ.get('DB_HOST'),
        'PORT': __os.environ.get('DB_PORT'),
        'DEBUG_NAME': 'default',
        'CONN_MAX_AGE': 600,
    },
}
print(f'Use Database: {DATABASES["default"]["NAME"]!r}', file=__sys.stderr)

MIDDLEWARE += ['findmydevice_project.middlewares.TracingMiddleware']

# _____________________________________________________________________________

if __os.environ.get('AUTOLOGIN') != '0':
    # Auto login for dev. server:
    MIDDLEWARE = MIDDLEWARE.copy()
    MIDDLEWARE += ['django_tools.middlewares.local_auto_login.AlwaysLoggedInAsSuperUserMiddleware']

# _____________________________________________________________________________
# Manage Django Project

INSTALLED_APPS.append('manage_django_project')

# _____________________________________________________________________________
# Django-Debug-Toolbar


INSTALLED_APPS.append('debug_toolbar')
MIDDLEWARE.append('debug_toolbar.middleware.DebugToolbarMiddleware')

DEBUG_TOOLBAR_PATCH_SETTINGS = True
from debug_toolbar.settings import CONFIG_DEFAULTS as DEBUG_TOOLBAR_CONFIG  # noqa


# Disable some more panels that will slow down the page:
DEBUG_TOOLBAR_CONFIG['DISABLE_PANELS'].add('debug_toolbar.panels.sql.SQLPanel')
DEBUG_TOOLBAR_CONFIG['DISABLE_PANELS'].add('debug_toolbar.panels.cache.CachePanel')

# don't load jquery from ajax.googleapis.com, just use django's version:
DEBUG_TOOLBAR_CONFIG['JQUERY_URL'] = STATIC_URL + 'admin/js/vendor/jquery/jquery.min.js'

DEBUG_TOOLBAR_CONFIG['SHOW_TEMPLATE_CONTEXT'] = True
DEBUG_TOOLBAR_CONFIG['SHOW_COLLAPSED'] = True  # Show toolbar collapsed by default.
DEBUG_TOOLBAR_CONFIG['SHOW_TOOLBAR_CALLBACK'] = 'findmydevice_project.middlewares.djdt_show'
