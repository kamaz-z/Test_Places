from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase

from apps.categories.models import Category
from apps.places.models import Place
from apps.reviews.models import Review

User = get_user_model()
PASSWORD = 'StrongPass-12345'


class ReviewTests(APITestCase):
    def setUp(self):
        self.place_owner = User.objects.create_user('powner', 'powner@example.com', PASSWORD)
        self.reviewer = User.objects.create_user('reviewer', 'reviewer@example.com', PASSWORD)
        self.other = User.objects.create_user('other', 'other@example.com', PASSWORD)
        self.admin = User.objects.create_user(
            'admin', 'admin@example.com', PASSWORD, is_staff=True
        )
        category = Category.objects.create(name='Parks', slug='parks')
        self.place = Place.objects.create(
            title='Central Park', description='Big park', category=category,
            address='NY', latitude='40.785091', longitude='-73.968285',
            author=self.place_owner,
        )
        self.list_url = f'/api/places/{self.place.pk}/reviews/'
        self.payload = {'rating': 5, 'comment': 'Great place'}

    def make_review(self):
        return Review.objects.create(
            place=self.place, author=self.reviewer, rating=4, comment='Nice'
        )

    def test_anonymous_can_list_but_not_create(self):
        self.assertEqual(self.client.get(self.list_url).status_code, status.HTTP_200_OK)
        r = self.client.post(self.list_url, self.payload)
        self.assertIn(r.status_code, (status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN))

    def test_create_review_sets_author_and_place(self):
        self.client.force_authenticate(self.reviewer)
        r = self.client.post(self.list_url, {**self.payload, 'author': self.other.pk})
        self.assertEqual(r.status_code, status.HTTP_201_CREATED)
        review = Review.objects.get(pk=r.data['id'])
        self.assertEqual(review.author, self.reviewer)
        self.assertEqual(review.place, self.place)
        self.assertEqual(r.data['likes_count'], 0)

    def test_duplicate_review_returns_409(self):
        self.client.force_authenticate(self.reviewer)
        self.assertEqual(self.client.post(self.list_url, self.payload).status_code, 201)
        r = self.client.post(self.list_url, self.payload)
        self.assertEqual(r.status_code, status.HTTP_409_CONFLICT)
        self.assertEqual(Review.objects.filter(place=self.place).count(), 1)

    def test_invalid_rating_rejected(self):
        self.client.force_authenticate(self.reviewer)
        for rating in (0, 6):
            with self.subTest(rating=rating):
                r = self.client.post(self.list_url, {'rating': rating, 'comment': 'x'})
                self.assertEqual(r.status_code, status.HTTP_400_BAD_REQUEST)

    def test_missing_or_deleted_place_returns_404(self):
        self.client.force_authenticate(self.reviewer)
        r = self.client.post('/api/places/999999/reviews/', self.payload)
        self.assertEqual(r.status_code, status.HTTP_404_NOT_FOUND)
        self.place.delete()
        self.assertEqual(self.client.post(self.list_url, self.payload).status_code, 404)
        self.assertEqual(self.client.get(self.list_url).status_code, 404)

    def test_owner_can_update(self):
        review = self.make_review()
        self.client.force_authenticate(self.reviewer)
        r = self.client.patch(f'/api/reviews/{review.pk}/', {'rating': 2})
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        review.refresh_from_db()
        self.assertEqual(review.rating, 2)

    def test_other_user_cannot_update_or_delete(self):
        review = self.make_review()
        self.client.force_authenticate(self.other)
        url = f'/api/reviews/{review.pk}/'
        self.assertEqual(self.client.patch(url, {'rating': 1}).status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(self.client.delete(url).status_code, status.HTTP_403_FORBIDDEN)

    def test_owner_and_admin_can_delete(self):
        review = self.make_review()
        self.client.force_authenticate(self.reviewer)
        self.assertEqual(self.client.delete(f'/api/reviews/{review.pk}/').status_code, 204)
        review = self.make_review()
        self.client.force_authenticate(self.admin)
        self.assertEqual(self.client.delete(f'/api/reviews/{review.pk}/').status_code, 204)

    def test_vote_and_counts(self):
        review = self.make_review()
        url = f'/api/reviews/{review.pk}/vote/'
        self.client.force_authenticate(self.other)
        r = self.client.post(url, {'value': 'like'})
        self.assertEqual(r.status_code, status.HTTP_201_CREATED)
        self.assertEqual(r.data['likes_count'], 1)
        self.client.force_authenticate(self.admin)
        r = self.client.post(url, {'value': 'dislike'})
        self.assertEqual((r.data['likes_count'], r.data['dislikes_count']), (1, 1))

    def test_second_vote_returns_409(self):
        review = self.make_review()
        url = f'/api/reviews/{review.pk}/vote/'
        self.client.force_authenticate(self.other)
        self.assertEqual(self.client.post(url, {'value': 'like'}).status_code, 201)
        self.assertEqual(self.client.post(url, {'value': 'like'}).status_code, 409)
        self.assertEqual(self.client.post(url, {'value': 'dislike'}).status_code, 409)

    def test_cannot_vote_own_review(self):
        review = self.make_review()
        self.client.force_authenticate(self.reviewer)
        r = self.client.post(f'/api/reviews/{review.pk}/vote/', {'value': 'like'})
        self.assertEqual(r.status_code, status.HTTP_403_FORBIDDEN)

    def test_anonymous_cannot_vote(self):
        review = self.make_review()
        r = self.client.post(f'/api/reviews/{review.pk}/vote/', {'value': 'like'})
        self.assertIn(r.status_code, (status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN))

    def test_invalid_vote_value(self):
        review = self.make_review()
        self.client.force_authenticate(self.other)
        r = self.client.post(f'/api/reviews/{review.pk}/vote/', {'value': 'meh'})
        self.assertEqual(r.status_code, status.HTTP_400_BAD_REQUEST)

    def test_review_of_deleted_place_hidden(self):
        review = self.make_review()
        self.place.delete()
        self.assertEqual(self.client.get(f'/api/reviews/{review.pk}/').status_code, 404) 