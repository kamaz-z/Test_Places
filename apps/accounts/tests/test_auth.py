from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.core import mail
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from rest_framework import status
from rest_framework.test import APITestCase

User = get_user_model()
PASSWORD = 'StrongPass-12345'


class AuthTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user('tarik', 'tarik@example.com', PASSWORD)

    def test_register_creates_user_and_logs_in(self):
        r = self.client.post('/api/auth/register/', {
            'username': 'new', 'email': 'new@example.com', 'password': PASSWORD,
        })
        self.assertEqual(r.status_code, status.HTTP_201_CREATED)
        self.assertEqual(self.client.get('/api/auth/me/').status_code, 200)

    def test_register_duplicate_email_case_insensitive(self):
        r = self.client.post('/api/auth/register/', {
            'username': 'other', 'email': 'TARIK@example.com', 'password': PASSWORD,
        })
        self.assertEqual(r.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('email', r.data)

    def test_register_weak_password_rejected(self):
        r = self.client.post('/api/auth/register/', {
            'username': 'weak', 'email': 'weak@example.com', 'password': '123',
        })
        self.assertEqual(r.status_code, status.HTTP_400_BAD_REQUEST)

    def test_login_logout_flow(self):
        r = self.client.post('/api/auth/login/', {'username': 'tarik', 'password': PASSWORD})
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        self.assertEqual(self.client.get('/api/auth/me/').data['username'], 'tarik')
        self.assertEqual(self.client.post('/api/auth/logout/').status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(self.client.get('/api/auth/me/').status_code, status.HTTP_403_FORBIDDEN)

    def test_login_wrong_password(self):
        r = self.client.post('/api/auth/login/', {'username': 'tarik', 'password': 'wrong'})
        self.assertEqual(r.status_code, status.HTTP_400_BAD_REQUEST)

    def test_password_reset_request_sends_email(self):
        r = self.client.post('/api/auth/password-reset/', {'email': 'tarik@example.com'})
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        self.assertEqual(len(mail.outbox), 1)

    def test_password_reset_unknown_email_same_response_no_mail(self):
        r = self.client.post('/api/auth/password-reset/', {'email': 'nobody@example.com'})
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        self.assertEqual(len(mail.outbox), 0)

    def test_password_reset_confirm(self):
        uid = urlsafe_base64_encode(force_bytes(self.user.pk))
        token = default_token_generator.make_token(self.user)
        new_password = 'Another-Pass-98765'
        r = self.client.post('/api/auth/password-reset/confirm/', {
            'uid': uid, 'token': token, 'new_password': new_password,
        })
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password(new_password))

    def test_password_reset_confirm_bad_token(self):
        uid = urlsafe_base64_encode(force_bytes(self.user.pk))
        r = self.client.post('/api/auth/password-reset/confirm/', {
            'uid': uid, 'token': 'bad-token', 'new_password': 'Another-Pass-98765',
        })
        self.assertEqual(r.status_code, status.HTTP_400_BAD_REQUEST)