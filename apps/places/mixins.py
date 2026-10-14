from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter

from core.filters import NullsLastOrderingFilter

from .filters import PlaceFilter
from .models import Place


class PlaceQueryMixin:
    """Same queryset + filters for the list endpoint and the export."""

    filter_backends = [DjangoFilterBackend, SearchFilter, NullsLastOrderingFilter]
    filterset_class = PlaceFilter
    search_fields = ('title', 'description')
    ordering_fields = ('created_at', 'avg_rating', 'popularity')
    ordering = ('-created_at',)

    def get_queryset(self):
        return Place.objects.select_related('category', 'author').with_popularity()