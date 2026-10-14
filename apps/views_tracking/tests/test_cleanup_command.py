from datetime import timedelta
from io import StringIO

from django.contrib.auth import get_user_model
from django.core.management import call_command, CommandError
from django.test import TestCase
from django.utils import timezone

from apps.categories.models import Category
from apps.places.models import Place
from apps.views_tracking.models import PlaceView


class CleanupPlaceViewsCommandTests(TestCase):
    def setUp(self):
        user = get_user_model().objects.create_user(
            'viewer', 'viewer@example.com', 'StrongPass-12345'
        )
        category = Category.objects.create(name='Parks', slug='parks')
        self.place = Place.objects.create(
            title='Central Park',
            description='Park',
            category=category,
            address='Somewhere',
            latitude='50.000000',
            longitude='30.000000',
            author=user,
        )

    def make_view(self, viewed_at):
        view = PlaceView.objects.create(place=self.place)
        PlaceView.objects.filter(pk=view.pk).update(viewed_at=viewed_at)
        return view

    def test_deletes_only_rows_older_than_days(self):
        old_view = self.make_view(timezone.now() - timedelta(days=31))
        recent_view = self.make_view(timezone.now() - timedelta(days=10))
        output = StringIO()

        call_command('cleanup_place_views', stdout=output)

        self.assertEqual(output.getvalue().strip(), 'Deleted 1 rows')
        self.assertFalse(PlaceView.objects.filter(pk=old_view.pk).exists())
        self.assertTrue(PlaceView.objects.filter(pk=recent_view.pk).exists())

    def test_rejects_days_below_popularity_window(self):
        with self.assertRaisesMessage(CommandError, '--days must be >= 7'):
            call_command('cleanup_place_views', days=6)

    def test_accepts_seven_day_minimum(self):
        output = StringIO()
        call_command('cleanup_place_views', days=7, stdout=output)
        self.assertEqual(output.getvalue().strip(), 'Deleted 0 rows')
