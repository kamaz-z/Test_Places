from django.core.cache import cache
from django.test import override_settings

LOCMEM_CACHES = {'default': {'BACKEND': 'django.core.cache.backends.locmem.LocMemCache'}}


def isolated_cache(cls):
    """Test-class decorator: local-memory cache, cleared before every test."""
    cls = override_settings(CACHES=LOCMEM_CACHES)(cls)
    original_setup = cls.setUp

    def setUp(self):
        cache.clear()
        original_setup(self)

    cls.setUp = setUp
    return cls
