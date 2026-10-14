import io
import json

import pandas as pd
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase

from apps.categories.models import Category
from apps.places.models import Place
from apps.reviews.models import Review
from core.testing import isolated_cache

User = get_user_model()
URL = '/api/export/places/'
PASSWORD = 'StrongPass-12345'


@isolated_cache
class ExportTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user('u', 'u@example.com', PASSWORD)
        self.reviewer = User.objects.create_user('r', 'r@example.com', PASSWORD)
        self.parks = Category.objects.create(name='Parks', slug='parks')
        self.museums = Category.objects.create(name='Museums', slug='museums')
        self.p1 = self.make('Парк Шевченка', self.parks)
        self.p2 = self.make('=cmd|calc', self.museums)
        Review.objects.create(place=self.p1, author=self.reviewer, rating=4, comment='x')

    def make(self, title, category):
        return Place.objects.create(
            title=title, description='d', category=category, address='a',
            latitude='50.000000', longitude='30.000000', author=self.user,
        )

    def test_json_export(self):
        r = self.client.get(f'{URL}?file_type=json')
        self.assertEqual(r.status_code, 200)
        self.assertIn('attachment', r['Content-Disposition'])
        data = json.loads(r.content)
        self.assertEqual(len(data), 2)
        row = next(x for x in data if x['title'] == 'Парк Шевченка')
        self.assertEqual((row['avg_rating'], row['reviews_count']), (4.0, 1))
        self.assertEqual(row['category_name'], 'Parks')

    def test_json_is_default(self):
        self.assertEqual(self.client.get(URL)['Content-Type'], 'application/json')

    def test_csv_export(self):
        r = self.client.get(f'{URL}?file_type=csv')
        self.assertEqual(r.status_code, 200)
        self.assertTrue(r['Content-Type'].startswith('text/csv'))
        df = pd.read_csv(io.StringIO(r.content.decode('utf-8-sig')))
        self.assertEqual(len(df), 2)
        self.assertEqual(list(df.columns)[:3], ['id', 'title', 'description'])
        self.assertIn('Парк Шевченка', set(df['title']))

    def test_csv_formula_injection_neutralized(self):
        r = self.client.get(f'{URL}?file_type=csv')
        df = pd.read_csv(io.StringIO(r.content.decode('utf-8-sig')))
        self.assertIn("'=cmd|calc", set(df['title']))

    def test_export_respects_filters_and_search(self):
        data = json.loads(self.client.get(f'{URL}?file_type=json&category={self.museums.pk}').content)
        self.assertEqual([x['title'] for x in data], ['=cmd|calc'])
        data = json.loads(self.client.get(f'{URL}?file_type=json&search=Шевченка').content)
        self.assertEqual(len(data), 1)

    def test_export_excludes_soft_deleted(self):
        self.p2.delete()
        self.assertEqual(len(json.loads(self.client.get(URL).content)), 1)

    def test_invalid_file_type(self):
        self.assertEqual(self.client.get(f'{URL}?file_type=xml').status_code, 400)