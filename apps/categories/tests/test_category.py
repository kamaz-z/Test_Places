from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase

from apps.categories.models import Category

User = get_user_model()
URL = '/api/categories/'


class CategoryTests(APITestCase):
    def setUp(self):
        self.admin = User.objects.create_user(
            'admin', 'admin@example.com', 'StrongPass-12345', is_staff=True
        )
        self.user = User.objects.create_user('user', 'user@example.com', 'StrongPass-12345')
        self.category = Category.objects.create(name='Parks', slug='parks')

    def test_anonymous_can_list(self):
        r = self.client.get(URL)
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        self.assertEqual(r.data['count'], 1)

    def test_anonymous_cannot_create(self):
        r = self.client.post(URL, {'name': 'Museums'})
        self.assertIn(r.status_code, (status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN))

    def test_regular_user_cannot_create(self):
        self.client.force_authenticate(self.user)
        r = self.client.post(URL, {'name': 'Museums'})
        self.assertEqual(r.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_can_create_and_slug_generated(self):
        self.client.force_authenticate(self.admin)
        r = self.client.post(URL, {'name': 'Street Art'})
        self.assertEqual(r.status_code, status.HTTP_201_CREATED)
        self.assertEqual(r.data['slug'], 'street-art')

    def test_duplicate_name_case_insensitive(self):
        self.client.force_authenticate(self.admin)
        r = self.client.post(URL, {'name': 'PARKS'})
        self.assertEqual(r.status_code, status.HTTP_400_BAD_REQUEST)

    def test_admin_can_update_and_delete(self):
        self.client.force_authenticate(self.admin)
        r = self.client.patch(f'{URL}{self.category.pk}/', {'name': 'City Parks'})
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        self.assertEqual(r.data['slug'], 'city-parks')
        r = self.client.delete(f'{URL}{self.category.pk}/')
        self.assertEqual(r.status_code, status.HTTP_204_NO_CONTENT)