from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from core.models import SoftDeleteModel, TimeStampedModel
from .managers import PlaceManager, PlaceQuerySet


class Place(SoftDeleteModel, TimeStampedModel):
    title = models.CharField(max_length=200)
    description = models.TextField()
    category = models.ForeignKey(
        'categories.Category', on_delete=models.PROTECT, related_name='places'
    )
    address = models.CharField(max_length=255)
    latitude = models.DecimalField(
        max_digits=9, decimal_places=6,
        validators=[MinValueValidator(-90), MaxValueValidator(90)],
    )
    longitude = models.DecimalField(
        max_digits=9, decimal_places=6,
        validators=[MinValueValidator(-180), MaxValueValidator(180)],
    )
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='places'
    )
    
    objects = PlaceManager()
    all_objects = models.Manager.from_queryset(PlaceQuerySet)()

    class Meta:
        ordering = ('-created_at',)

        indexes = [
            models.Index(fields=['latitude', 'longitude']),
        ]

        

    def __str__(self):
        return self.title