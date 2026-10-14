from django.urls import path
from rest_framework.routers import DefaultRouter

from apps.reviews.views import PlaceReviewListCreateView

from .views import PlaceViewSet

app_name = 'places'

router = DefaultRouter()
router.register('', PlaceViewSet, basename='place')

urlpatterns = [
    path(
        '<int:place_id>/reviews/',
        PlaceReviewListCreateView.as_view(),
        name='place-reviews',
    ),
    *router.urls,
]