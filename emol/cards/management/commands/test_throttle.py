"""Management command to test throttle middleware configuration."""

from django.conf import settings
from django.core.cache import cache
from django.core.management.base import BaseCommand
from django.test import RequestFactory
from global_throttle.middleware import GlobalThrottleMiddleware


class Command(BaseCommand):
    """Test throttle middleware configuration and behavior."""

    help = "Test the global throttle middleware configuration"

    def get_header_value(self, request, key):
        """Get the value of a header from the request."""
        value = request.META.get(key, "NOT SET")
        return f"   {key}: {repr(value)}"

    def handle(self, *args, **options):
        """Execute the test command."""
        self.stdout.write("🔍 Testing Global Throttle Middleware Configuration\n")

        # Check settings
        limit = getattr(settings, "GLOBAL_THROTTLE_LIMIT", "NOT SET")
        window = getattr(settings, "GLOBAL_THROTTLE_WINDOW", "NOT SET")
        django_settings_module = getattr(settings, "DJANGO_SETTINGS_MODULE", "NOT SET")

        self.stdout.write("📋 Settings:")
        self.stdout.write("   DJANGO_SETTINGS_MODULE: %s" % django_settings_module)
        self.stdout.write("   GLOBAL_THROTTLE_LIMIT: %s" % limit)
        self.stdout.write("   GLOBAL_THROTTLE_WINDOW: %s" % window)

        # Test middleware initialization
        self.stdout.write("\n🔧 Testing Middleware:")

        def dummy_response(request):
            return None

        middleware = GlobalThrottleMiddleware(dummy_response)
        self.stdout.write("   Middleware request_limit: %s" % middleware.request_limit)
        self.stdout.write(
            "   Middleware request_window: %s" % middleware.request_window
        )

        # Test with fake request
        factory = RequestFactory()
        request = factory.get("/")

        # Mock an anonymous user
        class MockUser:
            is_authenticated = False

        request.user = MockUser()

        self.stdout.write("\n🧪 Testing maybe_throttle:")
        result = middleware.maybe_throttle(request)
        self.stdout.write("   maybe_throttle() returned: %s" % result)

        if result is False:
            self.stdout.write(self.style.SUCCESS("✅ Request would NOT be throttled"))
        else:
            self.stdout.write(self.style.ERROR("❌ Request WOULD be throttled"))

        # Test IP address detection
        self.stdout.write("\n🌐 IP Address Detection:")
        self.stdout.write(self.get_header_value(request, "REMOTE_ADDR"))
        self.stdout.write(self.get_header_value(request, "HTTP_X_FORWARDED_FOR"))
        self.stdout.write(self.get_header_value(request, "HTTP_X_REAL_IP"))

        test_key = "throttle:global:127.0.0.1"
        cache_value = cache.get(test_key, "NOT FOUND")
        self.stdout.write("\n💾 Cache Test:")
        self.stdout.write("   Test cache key: %s" % test_key)
        self.stdout.write("   Current value: %s" % cache_value)

        # Test cache operations
        cache.set("test_throttle_cache", "working", 60)
        cache_test = cache.get("test_throttle_cache", "FAILED")
        self.stdout.write("   Cache write/read test: %s" % cache_test)

        # Check middleware list
        middleware_list = getattr(settings, "MIDDLEWARE", [])
        throttle_middleware = "global_throttle.middleware.GlobalThrottleMiddleware"

        self.stdout.write("\n📝 Middleware Configuration:")
        if throttle_middleware in middleware_list:
            index = middleware_list.index(throttle_middleware)
            self.stdout.write("   GlobalThrottleMiddleware is at position %s" % index)
            self.stdout.write("   Full middleware list:")
            for i, mw in enumerate(middleware_list):
                marker = (
                    " ← GlobalThrottleMiddleware" if mw == throttle_middleware else ""
                )
                self.stdout.write("     %s: %s%s" % (i, mw, marker))
        else:
            self.stdout.write(
                self.style.ERROR("   GlobalThrottleMiddleware NOT FOUND in MIDDLEWARE")
            )

        # Show a simulation of multiple requests
        self.stdout.write("\n🔄 Simulation (first 5 requests from same IP):")
        for i in range(5):
            result = middleware.maybe_throttle(request)
            self.stdout.write(
                f"   Request {i+1}: {'THROTTLED' if result else 'ALLOWED'}"
            )
