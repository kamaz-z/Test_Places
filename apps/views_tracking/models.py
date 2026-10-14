from django.conf import settings
from django.db import models


class PlaceView(models.Model):
    place = models.ForeignKey(
        'places.Place', on_delete=models.CASCADE, related_name='place_views'
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True,
        on_delete=models.SET_NULL, related_name='place_views',
    )
    viewed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=['place', 'viewed_at']),
            models.Index(fields=['viewed_at']),
        ]

    def __str__(self):
        return f'{self.place_id} @ {self.viewed_at:%Y-%m-%d %H:%M}'