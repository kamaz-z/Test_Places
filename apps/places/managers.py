from datetime import timedelta
from django.apps import apps
from django.db import models
from django.db.models import (
    Avg, Count, ExpressionWrapper, F, FloatField, IntegerField, OuterRef, Subquery, Value,
)
from django.db.models.functions import Cast, Coalesce, Ln
from django.utils import timezone

from core.models import SoftDeleteQuerySet

VIEWS_WINDOW_DAYS = 7
VIEW_WEIGHT = 0.1


class PlaceQuerySet(SoftDeleteQuerySet):
    def with_rating(self):
        Review = apps.get_model('reviews', 'Review')
        sub = (
            Review.objects.filter(place=OuterRef('pk'))
            .order_by().values('place')
            .annotate(v=Avg('rating')).values('v')
        )
        return self.annotate(avg_rating=Subquery(sub, output_field=FloatField()))

    def with_reviews_count(self):
        Review = apps.get_model('reviews', 'Review')
        sub = (
            Review.objects.filter(place=OuterRef('pk'))
            .order_by().values('place')
            .annotate(v=Count('pk')).values('v')
        )
        return self.annotate(
            reviews_count=Coalesce(Subquery(sub, output_field=IntegerField()), 0)
        )

    def with_views_7d(self):
        PlaceView = apps.get_model('views_tracking', 'PlaceView')
        since = timezone.now() - timedelta(days=VIEWS_WINDOW_DAYS)
        sub = (
            PlaceView.objects.filter(place=OuterRef('pk'), viewed_at__gte=since)
            .order_by().values('place')
            .annotate(v=Count('pk')).values('v')
        )
        return self.annotate(
            views_7d=Coalesce(Subquery(sub, output_field=IntegerField()), 0)
        )

    def with_popularity(self):
        qs = self.with_rating().with_reviews_count().with_views_7d()
        return qs.annotate(
            popularity=ExpressionWrapper(
                Coalesce(F('avg_rating'), Value(0.0))
                * Ln(Cast(1 + F('reviews_count'), FloatField()))
                + Cast(F('views_7d'), FloatField()) * VIEW_WEIGHT,
                output_field=FloatField(),
            )
        )


class PlaceManager(models.Manager.from_queryset(PlaceQuerySet)):
    """Hides soft-deleted rows by default."""

    def get_queryset(self):
        return super().get_queryset().filter(deleted_at__isnull=True)