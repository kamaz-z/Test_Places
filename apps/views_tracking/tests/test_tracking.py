from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import override_settings
from rest_framework.test import APITestCase

from apps.categories.models import Category
from apps.places.models import Place
from apps.views_tracking.models import PlaceView

User = get_user_model()
PASSWORD = 'StrongPass-12345'
LOCMEM = {'default': {'BACKEND': 'django.core.cache.backends.locmem.LocMemCache'}}


@override_settings(CACHES=LOCMEM)
class PlaceViewTrackingTests(APITestCase):
    def setUp(self):
        cache.clear()  # безпечно: тут локальний кеш, а не Redis з dev-даними
        self.user = User.objects.create_user('u1', 'u1@example.com', PASSWORD)
        self.user2 = User.objects.create_user('u2', 'u2@example.com', PASSWORD)
        category = Category.objects.create(name='Parks', slug='parks')
        self.place = Place.objects.create(
            title='Central Park', description='Big park', category=category,
            address='NY', latitude='40.785091', longitude='-73.968285', author=self.user,
        )
        self.url = f'/api/places/{self.place.pk}/'

    def count(self):
        return PlaceView.objects.filter(place=self.place).count()

    def test_retrieve_counts_view_for_authenticated_user(self):
        self.client.force_authenticate(self.user2)
        self.assertEqual(self.client.get(self.url).status_code, 200)
        self.assertEqual(self.count(), 1)
        self.assertEqual(PlaceView.objects.get().user, self.user2)

    def test_same_user_counted_once_per_hour(self):
        self.client.force_authenticate(self.user2)
        for _ in range(3):
            self.client.get(self.url)
        self.assertEqual(self.count(), 1)

    def test_view_counted_again_after_limit_expires(self):
        self.client.force_authenticate(self.user2)
        self.client.get(self.url)
        cache.clear()  # імітація спливання TTL
        self.client.get(self.url)
        self.assertEqual(self.count(), 2)

    def test_different_users_counted_separately(self):
        self.client.force_authenticate(self.user)
        self.client.get(self.url)
        self.client.force_authenticate(self.user2)
        self.client.get(self.url)
        self.assertEqual(self.count(), 2)

    def test_anonymous_limited_by_ip(self):
        self.client.get(self.url, REMOTE_ADDR='10.0.0.1')
        self.client.get(self.url, REMOTE_ADDR='10.0.0.1')
        self.assertEqual(self.count(), 1)
        self.client.get(self.url, REMOTE_ADDR='10.0.0.2')
        self.assertEqual(self.count(), 2)
        self.assertIsNone(PlaceView.objects.first().user)

    def test_list_does_not_count_views(self):
        self.client.force_authenticate(self.user2)
        self.client.get('/api/places/')
        self.assertEqual(self.count(), 0)

    def test_missing_or_deleted_place_not_counted(self):
        self.client.force_authenticate(self.user2)
        self.assertEqual(self.client.get('/api/places/999999/').status_code, 404)
        self.place.delete()
        self.assertEqual(self.client.get(self.url).status_code, 404)
        self.assertEqual(PlaceView.objects.count(), 0)