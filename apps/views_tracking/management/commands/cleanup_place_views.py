from datetime import timedelta

from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from apps.places.managers import VIEWS_WINDOW_DAYS
from apps.views_tracking.models import PlaceView


class Command(BaseCommand):
    help = 'Delete PlaceView rows older than N days (default 30, minimum 7).'

    def add_arguments(self, parser):
        parser.add_argument('--days', type=int, default=30)

    def handle(self, *args, **options):
        days = options['days']
        if days < VIEWS_WINDOW_DAYS:
            raise CommandError(
                f'--days must be >= {VIEWS_WINDOW_DAYS}: '
                'popularity uses a 7-day window.'
            )

        cutoff = timezone.now() - timedelta(days=days)
        deleted, _ = PlaceView.objects.filter(viewed_at__lt=cutoff).delete()
        self.stdout.write(f'Deleted {deleted} rows')
