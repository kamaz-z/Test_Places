from django.shortcuts import get_object_or_404
from rest_framework import generics, mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly
from rest_framework.response import Response

from apps.places.models import Place
from core.permissions import IsOwnerOrAdminOrReadOnly

from . import services
from .models import Review
from .serializers import ReviewSerializer, VoteSerializer


def annotated_reviews():
    return Review.objects.for_active_places().select_related('author').with_vote_counts()


class PlaceReviewListCreateView(generics.ListCreateAPIView):
    """GET/POST /api/places/{place_id}/reviews/"""
    serializer_class = ReviewSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get_place(self):
        return get_object_or_404(Place.objects.all(), pk=self.kwargs['place_id'])

    def get_queryset(self):
        place = self.get_place()  # 404, якщо локації немає або вона видалена
        return annotated_reviews().filter(place=place)

    def perform_create(self, serializer):
        review = services.create_review(
            author=self.request.user,
            place=self.get_place(),
            **serializer.validated_data,
        )
        serializer.instance = annotated_reviews().get(pk=review.pk)


class ReviewViewSet(
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet,
):
    """GET/PATCH/DELETE /api/reviews/{id}/ і POST /api/reviews/{id}/vote/"""
    serializer_class = ReviewSerializer
    permission_classes = [IsAuthenticatedOrReadOnly, IsOwnerOrAdminOrReadOnly]

    def get_queryset(self):
        return annotated_reviews()

    def perform_update(self, serializer):
        services.update_review(serializer.instance, **serializer.validated_data)

    def perform_destroy(self, instance):
        services.delete_review(instance)

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def vote(self, request, pk=None):
        review = self.get_object()
        serializer = VoteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        services.vote_review(
            user=request.user, review=review, value=serializer.validated_data['value']
        )
        review = self.get_queryset().get(pk=review.pk)
        return Response(ReviewSerializer(review).data, status=status.HTTP_201_CREATED)