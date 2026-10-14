from rest_framework import viewsets

from apps.places.cache import invalidate_places_list

from .models import Category
from .permissions import IsAdminOrReadOnly
from .serializers import CategorySerializer


class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [IsAdminOrReadOnly]
    search_fields = ('name',)

    def perform_create(self, serializer):
        super().perform_create(serializer)
        invalidate_places_list()

    def perform_update(self, serializer):
        super().perform_update(serializer)
        invalidate_places_list()

    def perform_destroy(self, instance):
        super().perform_destroy(instance)
        invalidate_places_list()