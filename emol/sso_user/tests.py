"""Tests for sso_user app."""

from io import StringIO
from unittest.mock import patch

from django.contrib.auth.models import AnonymousUser
from django.core.management import call_command
from django.http import HttpResponse
from django.test import Client, RequestFactory, TestCase, override_settings
from django.urls import reverse
from sso_user.decorators import admin_required, login_required
from sso_user.google_oauth import GoogleOAuth
from sso_user.models import SSOUser


class SSOUserModelTest(TestCase):
    """Tests for the SSOUser model."""

    def setUp(self):
        """Set up test fixtures."""
        self.user = SSOUser.objects.create(email="test@example.com")

    def test_user_creation(self):
        """Test basic user creation."""
        self.assertEqual(self.user.email, "test@example.com")
        self.assertFalse(self.user.is_superuser)
        self.assertFalse(self.user.is_staff)

    def test_user_manager(self):
        """Test user manager create methods."""
        user = SSOUser.objects.create_user(email="user@example.com")
        self.assertFalse(user.is_superuser)
        self.assertFalse(user.is_staff)

        superuser = SSOUser.objects.create_superuser(email="superuser@example.com")
        self.assertTrue(superuser.is_superuser)
        self.assertTrue(superuser.is_staff)


class GoogleOAuthTest(TestCase):
    def test_google_oauth_config(self):
        oauth = GoogleOAuth()
        self.assertEqual(
            oauth.CONF_URL,
            "https://accounts.google.com/.well-known/openid-configuration",
        )
        self.assertIn("openid", oauth.google.client_kwargs["scope"])
        self.assertIn("email", oauth.google.client_kwargs["scope"])
        self.assertIn("profile", oauth.google.client_kwargs["scope"])


class OAuthViewsTest(TestCase):
    def setUp(self):
        self.client = Client()

    def test_oauth_login(self):
        response = self.client.get(reverse("login"))
        self.assertEqual(response.status_code, 302)
        # In development/test mode, redirects to mock callback
        # In production, would redirect to Google OAuth
        if hasattr(response, "url") and response.url:
            self.assertTrue(
                "https://accounts.google.com/o/oauth2/v2/auth" in response.url
                or "/auth/mock_oauth_callback/" in response.url,
                f"Unexpected redirect URL: {response.url}",
            )

    def test_oauth_logout(self):
        response = self.client.get(reverse("logout"))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, "/")


class AdminOAuthViewTest(TestCase):
    """Tests for admin OAuth views."""

    def setUp(self):
        """Set up test fixtures."""
        self.client = Client()

    def test_admin_oauth(self):
        """Test admin OAuth redirect."""
        response = self.client.get(reverse("admin_oauth"))
        self.assertEqual(response.status_code, 302)
        if hasattr(response, "url") and response.url:
            self.assertTrue(
                "https://accounts.google.com/o/oauth2/v2/auth" in response.url
                or "/auth/mock_oauth_callback/" in response.url,
                f"Unexpected redirect URL: {response.url}",
            )


class LoginRequiredDecoratorTestCase(TestCase):
    """Tests for the login_required decorator."""

    def setUp(self):
        """Set up test fixtures."""
        self.factory = RequestFactory()
        self.user = SSOUser.objects.create_user(email="test@example.com")

    def test_login_required_allows_authenticated_user(self):
        """Authenticated user can access decorated view."""

        @login_required
        def test_view(request):
            return HttpResponse("OK")

        request = self.factory.get("/test/")
        request.user = self.user

        with patch("sso_user.decorators.get_current_user", return_value=self.user):
            response = test_view(request)

        self.assertEqual(response.status_code, 200)

    def test_login_required_redirects_anonymous_user(self):
        """Anonymous user is redirected to login."""

        @login_required
        def test_view(request):
            return HttpResponse("OK")

        request = self.factory.get("/test/")
        request.user = AnonymousUser()

        with patch("sso_user.decorators.get_current_user", return_value=None):
            response = test_view(request)

        self.assertEqual(response.status_code, 302)


class AdminRequiredDecoratorTestCase(TestCase):
    """Tests for the admin_required decorator."""

    def setUp(self):
        """Set up test fixtures."""
        self.factory = RequestFactory()
        self.admin = SSOUser.objects.create_superuser(email="admin@example.com")
        self.user = SSOUser.objects.create_user(email="user@example.com")

    def test_admin_required_allows_superuser(self):
        """Superuser can access decorated view."""

        @admin_required
        def test_view(request):
            return HttpResponse("OK")

        request = self.factory.get("/test/")
        request.user = self.admin

        with patch("sso_user.decorators.get_current_user", return_value=self.admin):
            response = test_view(request)

        self.assertEqual(response.status_code, 200)

    def test_admin_required_denies_regular_user(self):
        """Regular user is denied access."""

        @admin_required
        def test_view(request):
            return HttpResponse("OK")

        request = self.factory.get("/test/")
        request.user = self.user

        with patch("sso_user.decorators.get_current_user", return_value=self.user):
            response = test_view(request)

        self.assertEqual(response.status_code, 401)

    def test_admin_required_denies_anonymous(self):
        """Anonymous user is denied access."""

        @admin_required
        def test_view(request):
            return HttpResponse("OK")

        request = self.factory.get("/test/")
        request.user = AnonymousUser()

        with patch("sso_user.decorators.get_current_user", return_value=None):
            response = test_view(request)

        self.assertEqual(response.status_code, 401)


class EnsureSuperuserCommandTestCase(TestCase):
    """Tests for the ensure_superuser management command."""

    def test_does_nothing_if_superuser_exists(self):
        """Command exits early if superuser already exists."""
        SSOUser.objects.create_superuser(email="existing@example.com")
        out = StringIO()

        call_command("ensure_superuser", stdout=out)

        self.assertIn("already exists", out.getvalue())

    @override_settings(EMOL_DEV=True)
    def test_creates_superuser_with_email_argument(self):
        """Command creates superuser with provided email."""
        out = StringIO()

        call_command(
            "ensure_superuser",
            email="new@example.com",
            non_interactive=True,
            stdout=out,
        )

        self.assertTrue(SSOUser.objects.filter(email="new@example.com").exists())
        user = SSOUser.objects.get(email="new@example.com")
        self.assertTrue(user.is_superuser)

    @patch.dict("os.environ", {"SUPERUSER_EMAIL": "env@example.com"})
    def test_creates_superuser_from_env_var(self):
        """Command uses SUPERUSER_EMAIL environment variable."""
        out = StringIO()

        call_command("ensure_superuser", non_interactive=True, stdout=out)

        self.assertTrue(SSOUser.objects.filter(email="env@example.com").exists())

    @patch.dict("os.environ", {"EMOL_DEV": "1"})
    def test_uses_default_email_in_dev_mode(self):
        """Command uses default email in EMOL_DEV mode."""
        out = StringIO()

        call_command("ensure_superuser", non_interactive=True, stdout=out)

        self.assertTrue(SSOUser.objects.filter(email="admin@emol.com").exists())
