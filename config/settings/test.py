"""Settings for automated tests."""

from .base import *

DEBUG = False
ALLOWED_HOSTS = [*ALLOWED_HOSTS, 'testserver']

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'test-cache',
    },
}
