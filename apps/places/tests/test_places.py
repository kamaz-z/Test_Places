from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase

from apps.categories.models import Category
from apps.places.models import Place

User = get_user_model()
URL = '/api/places/'
PASSWORD = 'StrongPass-12345'


class PlaceTests(APITestCase):
    def setUp(self):
        self.owner = User.objects.create_user('owner', 'owner@example.com', PASSWORD)
        self.other = User.objects.create_user('other', 'other@example.com', PASSWORD)
        self.admin = User.objects.create_user(
            'admin', 'admin@example.com', PASSWORD, is_staff=True
        )
        self.category = Category.objects.create(name='Parks', slug='parks')
        self.place = Place.objects.create(
            title='Central Park', description='Big park', category=self.category,
            address='NY', latitude='40.785091', longitude='-73.968285', author=self.owner,
        )
        self.payload = {
            'title': 'New place', 'description': 'Desc', 'category': self.category.pk,
            'address': 'Somewhere', 'latitude': '50.450100', 'longitude': '30.523400',
        }

    def test_anonymous_can_list_and_retrieve(self):
        self.assertEqual(self.client.get(URL).status_code, status.HTTP_200_OK)
        self.assertEqual(self.client.get(f'{URL}{self.place.pk}/').status_code, status.HTTP_200_OK)

    def test_anonymous_cannot_create(self):
        r = self.client.post(URL, self.payload)
        self.assertIn(r.status_code, (status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN))

    def test_create_sets_author_from_request(self):
        self.client.force_authenticate(self.other)
        r = self.client.post(URL, {**self.payload, 'author': self.owner.pk})
        self.assertEqual(r.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Place.objects.get(pk=r.data['id']).author, self.other)

    def test_invalid_coordinates_rejected(self):
        self.client.force_authenticate(self.owner)
        r = self.client.post(URL, {**self.payload, 'latitude': '123.0'})
        self.assertEqual(r.status_code, status.HTTP_400_BAD_REQUEST)

    def test_owner_can_update(self):
        self.client.force_authenticate(self.owner)
        r = self.client.patch(f'{URL}{self.place.pk}/', {'title': 'Renamed'})
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        self.assertEqual(r.data['title'], 'Renamed')
        self.place.refresh_from_db()
        self.assertEqual(self.place.title, 'Renamed')

    def test_other_user_cannot_update_or_delete(self):
        self.client.force_authenticate(self.other)
        url = f'{URL}{self.place.pk}/'
        self.assertEqual(self.client.patch(url, {'title': 'Hack'}).status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(self.client.delete(url).status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_can_delete_foreign_place(self):
        self.client.force_authenticate(self.admin)
        r = self.client.delete(f'{URL}{self.place.pk}/')
        self.assertEqual(r.status_code, status.HTTP_204_NO_CONTENT)

    def test_delete_is_soft(self):
        self.client.force_authenticate(self.owner)
        r = self.client.delete(f'{URL}{self.place.pk}/')
        self.assertEqual(r.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Place.objects.filter(pk=self.place.pk).exists())
        deleted_place = Place.all_objects.get(pk=self.place.pk)
        self.assertIsNotNone(deleted_place.deleted_at)
        self.assertEqual(self.client.get(f'{URL}{self.place.pk}/').status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(self.client.get(URL).data['count'], 0)