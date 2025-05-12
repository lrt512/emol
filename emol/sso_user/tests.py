# tests.py
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model

from .models import SSOUser
from .google_oauth import GoogleOAuth

class SSOUserModelTest(TestCase):
    def setUp(self):
        self.user = SSOUser.objects.create(email='test@example.com')

    def test_user_creation(self):
        self.assertEqual(self.user.email, 'test@example.com')
        self.assertFalse(self.user.is_superuser)
        self.assertFalse(self.user.is_staff)

    def test_user_manager(self):
        user = SSOUser.objects.create_user(email='user@example.com')
        self.assertFalse(user.is_superuser)
        self.assertFalse(user.is_staff)

        superuser = SSOUser.objects.create_superuser(email='superuser@example.com')
        self.assertTrue(superuser.is_superuser)
        self.assertTrue(superuser.is_staff)

class GoogleOAuthTest(TestCase):
    def test_google_oauth_config(self):
        oauth = GoogleOAuth()
        self.assertEqual(oauth.CONF_URL, 'https://accounts.google.com/.well-known/openid-configuration')
        self.assertIn('openid', oauth.google.client_kwargs['scope'])
        self.assertIn('email', oauth.google.client_kwargs['scope'])
        self.assertIn('profile', oauth.google.client_kwargs['scope'])

class OAuthViewsTest(TestCase):
    def setUp(self):
        self.client = Client()

    def test_oauth_login(self):
        response = self.client.get(reverse('login'))
        self.assertEqual(response.status_code, 302)
        self.assertIn('https://accounts.google.com/o/oauth2/v2/auth', response.url)

    def test_oauth_logout(self):
        response = self.client.get(reverse('logout'))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, '/')

class AdminOAuthViewTest(TestCase):
    def setUp(self):
        self.client = Client()

    def test_admin_oauth(self):
        response = self.client.get(reverse('admin_oauth'))
        self.assertEqual(response.status_code, 302)
        self.assertIn('https://accounts.google.com/o/oauth2/v2/auth', response.url)
