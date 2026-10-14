from django.test import SimpleTestCase
from django.urls import reverse


class ReviewRoutesTests(SimpleTestCase):
    def test_review_detail_route_is_available(self):
        self.assertEqual(
            reverse('reviews:review-detail', kwargs={'pk': 1}),
            '/api/reviews/1/',
        )

    def test_place_reviews_route_is_available(self):
        self.assertEqual(
            reverse('places:place-reviews', kwargs={'place_id': 1}),
            '/api/places/1/reviews/',
        )
