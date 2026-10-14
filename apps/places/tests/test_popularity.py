import math
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import override_settings
from django.utils import timezone
from rest_framework.test import APITestCase

from apps.categories.models import Category
from apps.places.models import Place
from apps.reviews.models import Review
from apps.views_tracking.models import PlaceView

User = get_user_model()
PASSWORD = 'StrongPass-12345'
LOCMEM = {'default': {'BACKEND': 'django.core.cache.backends.locmem.LocMemCache'}}


@override_settings(CACHES=LOCMEM)
class PopularityTests(APITestCase):
    def setUp(self):
        cache.clear()
        self.users = [
            User.objects.create_user(f'u{i}', f'u{i}@example.com', PASSWORD) for i in range(4)
        ]
        self.category = Category.objects.create(name='Parks', slug='parks')

    def make_place(self, title='P'):
        return Place.objects.create(
            title=title, description='d', category=self.category, address='a',
            latitude='50.000000', longitude='30.000000', author=self.users[0],
        )

    def annotated(self, place):
        return Place.objects.with_popularity().get(pk=place.pk)

    def test_no_reviews_no_views(self):
        p = self.annotated(self.make_place())
        self.assertIsNone(p.avg_rating)
        self.assertEqual((p.reviews_count, p.views_7d), (0, 0))
        self.assertEqual(p.popularity, 0)

    def test_counts_not_inflated_by_join(self):
        place = self.make_place()
        Review.objects.create(place=place, author=self.users[1], rating=5, comment='a')
        Review.objects.create(place=place, author=self.users[2], rating=3, comment='b')
        PlaceView.objects.bulk_create([PlaceView(place=place) for _ in range(4)])
        p = self.annotated(place)
        self.assertEqual(p.reviews_count, 2)
        self.assertEqual(p.views_7d, 4)
        self.assertAlmostEqual(p.avg_rating, 4.0)

    def test_popularity_formula(self):
        place = self.make_place()
        Review.objects.create(place=place, author=self.users[1], rating=5, comment='a')
        Review.objects.create(place=place, author=self.users[2], rating=3, comment='b')
        PlaceView.objects.bulk_create([PlaceView(place=place) for _ in range(4)])
        expected = 4.0 * math.log(1 + 2) + 0.1 * 4
        self.assertAlmostEqual(self.annotated(place).popularity, expected, places=5)

    def test_views_older_than_7_days_ignored(self):
        place = self.make_place()
        old = PlaceView.objects.create(place=place)
        PlaceView.objects.filter(pk=old.pk).update(viewed_at=timezone.now() - timedelta(days=8))
        PlaceView.objects.create(place=place)
        self.assertEqual(self.annotated(place).views_7d, 1)

    def test_more_reviews_beat_single_perfect_review(self):
        single = self.make_place('single')
        many = self.make_place('many')
        Review.objects.create(place=single, author=self.users[1], rating=5, comment='x')
        for user in self.users[1:]:
            Review.objects.create(place=many, author=user, rating=4, comment='x')
        ranked = list(Place.objects.with_popularity().order_by('-popularity'))
        self.assertEqual(ranked[0].pk, many.pk)

    def test_api_returns_computed_fields(self):
        place = self.make_place()
        Review.objects.create(place=place, author=self.users[1], rating=4, comment='x')
        r = self.client.get(f'/api/places/{place.pk}/')
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.data['avg_rating'], 4.0)
        self.assertEqual(r.data['reviews_count'], 1)
        self.assertIn('popularity', r.data)

    def test_create_response_has_computed_fields(self):
        self.client.force_authenticate(self.users[1])
        r = self.client.post('/api/places/', {
            'title': 'New', 'description': 'd', 'category': self.category.pk,
            'address': 'a', 'latitude': '50.4501', 'longitude': '30.5234',
        })
        self.assertEqual(r.status_code, 201)
        self.assertEqual(r.data['reviews_count'], 0)
        self.assertIsNone(r.data['avg_rating'])