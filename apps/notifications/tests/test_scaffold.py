from django.test import SimpleTestCase
from django.urls import reverse


class NotificationRoutesTests(SimpleTestCase):
    def test_subscriptions_route_is_available(self):
        self.assertEqual(reverse('notifications:subscriptions'), '/api/notifications/')
