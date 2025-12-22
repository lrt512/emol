import time

from django.contrib.auth.models import AnonymousUser
from django.core.cache import cache
from django.test import RequestFactory, TestCase
from django.test.utils import override_settings
from django.urls import path, reverse
from global_throttle.decorators import exempt_from_throttling
from global_throttle.middleware import GlobalThrottleMiddleware
from sso_user.models.user import SSOUser


@exempt_from_throttling
def exempt_view(request):
    return None


def non_exempt_view(request):
    return None


urlpatterns = [
    path("exempt/", exempt_view, name="exempt_view"),
    path("non_exempt/", non_exempt_view, name="non_exempt_view"),
]


@override_settings(ROOT_URLCONF=__name__)
class GlobalThrottleMiddlewareTestCase(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.middleware = GlobalThrottleMiddleware(lambda request: None)
        self.user = SSOUser.objects.create_user(email="test@example.com")

    def tearDown(self):
        cache.clear()

    def test_authenticated_user_not_throttled(self):
        """Test that authenticated users are not throttled"""
        request = self.factory.get("/")
        request.user = self.user
        self.assertFalse(self.middleware.maybe_throttle(request))

    @override_settings(GLOBAL_THROTTLE_LIMIT=10)
    def test_anonymous_user_throttled(self):
        """Test that anonymous users are throttled"""
        middleware = GlobalThrottleMiddleware(lambda request: None)
        request = self.factory.get(reverse("non_exempt_view"))
        request.user = AnonymousUser()
        request.META["REMOTE_ADDR"] = "192.168.1.100"  # Non-whitelisted IP
        for _ in range(10):
            self.assertFalse(middleware.maybe_throttle(request))
        self.assertTrue(middleware.maybe_throttle(request))

    @override_settings(GLOBAL_THROTTLE_LIMIT=10)
    def test_anonymous_user_throttle_reset(self):
        """Test that anonymous users are throttled and reset after a period of time"""
        middleware = GlobalThrottleMiddleware(lambda request: None)
        request = self.factory.get(reverse("non_exempt_view"))
        request.user = AnonymousUser()
        request.META["REMOTE_ADDR"] = "192.168.1.101"  # Non-whitelisted IP
        for _ in range(10):
            self.assertFalse(middleware.maybe_throttle(request))
        self.assertTrue(middleware.maybe_throttle(request))
        cache.clear()
        self.assertFalse(middleware.maybe_throttle(request))

    @override_settings(GLOBAL_THROTTLE_LIMIT=10)
    def test_exempt_view_not_throttled(self):
        """Test that exempt views are not throttled"""
        middleware = GlobalThrottleMiddleware(lambda request: None)
        request = self.factory.get(reverse("exempt_view"))
        request.user = AnonymousUser()
        request.META["REMOTE_ADDR"] = "192.168.1.104"  # Non-whitelisted IP
        for _ in range(15):
            self.assertFalse(middleware.maybe_throttle(request))

    @override_settings(GLOBAL_THROTTLE_LIMIT=20)
    def test_throttle_limit_override(self):
        """Test that the throttle limit can be overridden in settings.py

        Need to use a fresh middleware to pick up the new settings.
        """
        middleware = GlobalThrottleMiddleware(lambda request: None)
        request = self.factory.get(reverse("non_exempt_view"))
        request.user = AnonymousUser()
        request.META["REMOTE_ADDR"] = "192.168.1.102"  # Non-whitelisted IP
        for _ in range(20):
            self.assertFalse(middleware.maybe_throttle(request))
        self.assertTrue(middleware.maybe_throttle(request))

    @override_settings(GLOBAL_THROTTLE_LIMIT=10, GLOBAL_THROTTLE_WINDOW=2)
    def test_throttle_window(self):
        """Test that the throttle window resets after the specified time

        Using a much shorter throttle window than the default!
        """
        middleware = GlobalThrottleMiddleware(lambda request: None)

        request = self.factory.get(reverse("non_exempt_view"))
        request.user = AnonymousUser()
        request.META["REMOTE_ADDR"] = "192.168.1.103"  # Non-whitelisted IP

        for _ in range(10):
            self.assertFalse(middleware.maybe_throttle(request))
        self.assertTrue(middleware.maybe_throttle(request))

        # Reset the window
        time.sleep(2)
        self.assertFalse(middleware.maybe_throttle(request))


@override_settings(ROOT_URLCONF=__name__)
class ExemptFromThrottlingDecoratorTestCase(TestCase):
    def setUp(self):
        self.factory = RequestFactory()

    def test_exempt_view_has_exempt_attribute(self):
        """Test that the exempt_from_throttling decorator adds an
        exempt_from_throttling attribute to the view function"""
        view_func = exempt_view
        self.assertTrue(getattr(view_func, "exempt_from_throttling", False))

    def test_non_exempt_view_does_not_have_exempt_attribute(self):
        """Test that views without the exempt_from_throttling decorator do not"""
        view_func = non_exempt_view
        self.assertFalse(getattr(view_func, "exempt_from_throttling", False))
