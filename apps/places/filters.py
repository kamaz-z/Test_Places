import django_filters
from .models import Place


class PlaceFilter(django_filters.FilterSet):
    category = django_filters.NumberFilter(field_name='category_id')
    category_slug = django_filters.CharFilter(field_name='category__slug')
    author = django_filters.NumberFilter(field_name='author_id')
    author_username = django_filters.CharFilter(field_name='author__username', lookup_expr='iexact')
    min_rating = django_filters.NumberFilter(field_name='avg_rating', lookup_expr='gte')
    max_rating = django_filters.NumberFilter(field_name='avg_rating', lookup_expr='lte')

    class Meta:
        model = Place
        fields = []
