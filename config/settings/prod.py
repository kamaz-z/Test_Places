"""Settings for production deployments."""

from django.core.exceptions import ImproperlyConfigured

from .base import *

DEBUG = False
if not ALLOWED_HOSTS:
    raise ImproperlyConfigured('Set DJANGO_ALLOWED_HOSTS to a comma-separated host list.')
