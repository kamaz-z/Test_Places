from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase

from apps.categories.models import Category
from apps.places.models import Place
from core.testing import isolated_cache

User = get_user_model()
URL = '/api/places/'
PASSWORD = 'StrongPass-12345'


@isolated_cache
class PlaceListCacheTests(APITestCase):
    def setUp(self):
        self.owner = User.objects.create_user('owner', 'owner@example.com', PASSWORD)
        self.other = User.objects.create_user('other', 'other@example.com', PASSWORD)
        self.admin = User.objects.create_user(
            'admin', 'admin@example.com', PASSWORD, is_staff=True
        )
        self.category = Category.objects.create(name='Parks', slug='parks')
        self.place = Place.objects.create(
            title='Central Park',
            description='d',
            category=self.category,
            address='a',
            latitude='40.000000',
            longitude='-73.000000',
            author=self.owner,
        )

    def results(self, query=''):
        return self.client.get(f'{URL}{query}').data['results']

    def test_second_request_served_from_cache(self):
        self.client.get(URL)
        with self.assertNumQueries(0):
            self.assertEqual(self.client.get(URL).data['count'], 1)

    def test_different_params_cached_separately(self):
        self.assertEqual(len(self.results()), 1)
        self.assertEqual(len(self.results('?search=nothing-like-this')), 0)
        self.assertEqual(len(self.results()), 1)

    def test_create_invalidates(self):
        self.results()
        self.client.force_authenticate(self.other)
        response = self.client.post(URL, {
            'title': 'New',
            'description': 'd',
            'category': self.category.pk,
            'address': 'a',
            'latitude': '50.4501',
            'longitude': '30.5234',
        })
        self.assertEqual(response.status_code, 201)
        self.assertEqual(len(self.results()), 2)

    def test_update_invalidates(self):
        self.results()
        self.client.force_authenticate(self.owner)
        self.client.patch(f'{URL}{self.place.pk}/', {'title': 'Renamed'})
        self.assertEqual(self.results()[0]['title'], 'Renamed')

    def test_delete_invalidates(self):
        self.results()
        self.client.force_authenticate(self.owner)
        self.client.delete(f'{URL}{self.place.pk}/')
        self.assertEqual(len(self.results()), 0)

    def test_new_review_invalidates(self):
        self.assertEqual(self.results()[0]['reviews_count'], 0)
        self.client.force_authenticate(self.other)
        response = self.client.post(
            f'{URL}{self.place.pk}/reviews/',
            {'rating': 5, 'comment': 'x'},
        )
        self.assertEqual(response.status_code, 201)
        item = self.results()[0]
        self.assertEqual((item['reviews_count'], item['avg_rating']), (1, 5.0))

    def test_review_update_and_delete_invalidate(self):
        self.client.force_authenticate(self.other)
        review_id = self.client.post(
            f'{URL}{self.place.pk}/reviews/',
            {'rating': 5, 'comment': 'x'},
        ).data['id']
        self.assertEqual(self.results()[0]['avg_rating'], 5.0)
        self.client.patch(f'/api/reviews/{review_id}/', {'rating': 1})
        self.assertEqual(self.results()[0]['avg_rating'], 1.0)
        self.client.delete(f'/api/reviews/{review_id}/')
        self.assertEqual(self.results()[0]['reviews_count'], 0)

    def test_category_rename_invalidates(self):
        self.assertEqual(self.results()[0]['category_detail']['name'], 'Parks')
        self.client.force_authenticate(self.admin)
        self.client.patch(
            f'/api/categories/{self.category.pk}/',
            {'name': 'Gardens'},
        )
        self.assertEqual(self.results()[0]['category_detail']['name'], 'Gardens')
