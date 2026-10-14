import hashlib
import uuid

from django.core.cache import cache

VERSION_KEY = 'places:list:version'
LIST_TTL = 60  # секунд


def _get_version() -> str:
    version = cache.get(VERSION_KEY)
    if version is None:
        cache.add(VERSION_KEY, uuid.uuid4().hex, timeout=None)
        version = cache.get(VERSION_KEY)
    return version


def build_list_key(request) -> str:
    params = sorted((k, tuple(v)) for k, v in request.query_params.lists())
    digest = hashlib.sha256(repr(params).encode()).hexdigest()
    return f'places:list:{_get_version()}:{digest}'


def invalidate_places_list() -> None:
    cache.set(VERSION_KEY, uuid.uuid4().hex, timeout=None)