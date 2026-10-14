from django.core.cache import cache
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from rest_framework.response import Response

from apps.views_tracking import services as views_services
from core.permissions import IsOwnerOrAdminOrReadOnly

from . import cache as places_cache
from . import services
from .mixins import PlaceQueryMixin
from .serializers import PlaceSerializer


class PlaceViewSet(PlaceQueryMixin, viewsets.ModelViewSet):
    serializer_class = PlaceSerializer
    permission_classes = [IsAuthenticatedOrReadOnly, IsOwnerOrAdminOrReadOnly]

    def list(self, request, *args, **kwargs):
        key = places_cache.build_list_key(request)
        data = cache.get(key)
        if data is None:
            response = super().list(request, *args, **kwargs)
            cache.set(key, response.data, places_cache.LIST_TTL)
            return response
        return Response(data)

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        views_services.register_view(place=instance, request=request)
        return Response(self.get_serializer(instance).data)

    def perform_create(self, serializer):
        place = services.create_place(author=self.request.user, **serializer.validated_data)
        serializer.instance = self.get_queryset().get(pk=place.pk)

    def perform_update(self, serializer):
        services.update_place(serializer.instance, **serializer.validated_data)

    def perform_destroy(self, instance):
        services.delete_place(instance)