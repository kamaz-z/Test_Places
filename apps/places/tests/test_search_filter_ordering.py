from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase

from apps.categories.models import Category
from apps.places.models import Place
from apps.reviews.models import Review
from core.testing import isolated_cache

User = get_user_model()
URL = '/api/places/'
PASSWORD = 'StrongPass-12345'


@isolated_cache
class PlaceListQueryTests(APITestCase):
    def setUp(self):
        self.u = [
            User.objects.create_user(f'u{i}', f'u{i}@example.com', PASSWORD)
            for i in range(4)
        ]
        self.parks = Category.objects.create(name='Parks', slug='parks')
        self.museums = Category.objects.create(name='Museums', slug='museums')
        self.a = self.make('Alpha Park', 'quiet', self.parks, self.u[0])
        self.b = self.make('Beta', 'big park with lake', self.parks, self.u[0])
        self.c = self.make('Gamma', 'museum', self.museums, self.u[1])
        Review.objects.create(
            place=self.a, author=self.u[1], rating=5, comment='x'
        )
        for user in self.u[1:]:
            Review.objects.create(place=self.b, author=user, rating=3, comment='x')

    def make(self, title, description, category, author):
        return Place.objects.create(
            title=title,
            description=description,
            category=category,
            address='a',
            latitude='50.000000',
            longitude='30.000000',
            author=author,
        )

    def titles(self, query=''):
        response = self.client.get(f'{URL}{query}')
        self.assertEqual(response.status_code, 200)
        return [place['title'] for place in response.data['results']]

    def test_search_title_and_description(self):
        self.assertCountEqual(self.titles('?search=park'), ['Alpha Park', 'Beta'])
        self.assertEqual(self.titles('?search=museum'), ['Gamma'])

    def test_filter_by_category(self):
        self.assertEqual(self.titles(f'?category={self.museums.pk}'), ['Gamma'])
        self.assertCountEqual(
            self.titles('?category_slug=parks'), ['Alpha Park', 'Beta']
        )

    def test_filter_by_author(self):
        self.assertEqual(self.titles(f'?author={self.u[1].pk}'), ['Gamma'])

    def test_filter_by_rating(self):
        self.assertEqual(self.titles('?min_rating=4'), ['Alpha Park'])
        self.assertEqual(self.titles('?max_rating=3.5'), ['Beta'])

    def test_default_ordering_newest_first(self):
        self.assertEqual(self.titles(), ['Gamma', 'Beta', 'Alpha Park'])
        self.assertEqual(
            self.titles('?ordering=created_at'), ['Alpha Park', 'Beta', 'Gamma']
        )

    def test_ordering_by_rating_nulls_last(self):
        self.assertEqual(
            self.titles('?ordering=-avg_rating'), ['Alpha Park', 'Beta', 'Gamma']
        )
        self.assertEqual(
            self.titles('?ordering=avg_rating'), ['Beta', 'Alpha Park', 'Gamma']
        )

    def test_ordering_by_popularity(self):
        self.assertEqual(
            self.titles('?ordering=-popularity'), ['Beta', 'Alpha Park', 'Gamma']
        )

    def test_unknown_ordering_field_ignored(self):
        self.assertEqual(
            self.titles('?ordering=password'), ['Gamma', 'Beta', 'Alpha Park']
        )

    def test_pagination(self):
        response = self.client.get(f'{URL}?page_size=2')
        self.assertEqual(response.status_code, 200)
        self.assertEqual((response.data['count'], len(response.data['results'])), (3, 2))