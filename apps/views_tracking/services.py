from django.core.cache import cache

from .models import PlaceView

VIEW_TTL_SECONDS = 60 * 60


def _viewer_id(request) -> str:
    user = request.user
    if user.is_authenticated:
        return f'u{user.pk}'
    return f'ip{request.META.get("REMOTE_ADDR", "unknown")}'


def register_view(*, place, request) -> bool:
    """Count a view at most once per hour per viewer. Returns True if counted."""
    key = f'place_view:{place.pk}:{_viewer_id(request)}'
    if not cache.add(key, 1, timeout=VIEW_TTL_SECONDS):  # атомарний SET NX EX
        return False
    try:
        PlaceView.objects.create(
            place=place,
            user=request.user if request.user.is_authenticated else None,
        )
    except Exception:
        cache.delete(key)  # не блокуємо ліміт, якщо запис не вдався
        raise
    return True