"""Management command to test throttle middleware configuration."""

from django.core.management.base import BaseCommand
from django.conf import settings
from django.test import RequestFactory
from global_throttle.middleware import GlobalThrottleMiddleware


class Command(BaseCommand):
    """Test throttle middleware configuration and behavior."""
    
    help = "Test the global throttle middleware configuration"

    def handle(self, *args, **options):
        """Execute the test command."""
        self.stdout.write("🔍 Testing Global Throttle Middleware Configuration\n")
        
        # Check settings
        limit = getattr(settings, "GLOBAL_THROTTLE_LIMIT", "NOT SET")
        window = getattr(settings, "GLOBAL_THROTTLE_WINDOW", "NOT SET")
        django_settings_module = getattr(settings, "DJANGO_SETTINGS_MODULE", "NOT SET")
        
        self.stdout.write(f"📋 Settings:")
        self.stdout.write(f"   DJANGO_SETTINGS_MODULE: {django_settings_module}")
        self.stdout.write(f"   GLOBAL_THROTTLE_LIMIT: {limit}")
        self.stdout.write(f"   GLOBAL_THROTTLE_WINDOW: {window}")
        
        # Test middleware initialization
        self.stdout.write(f"\n🔧 Testing Middleware:")
        
        def dummy_response(request):
            return None
            
        middleware = GlobalThrottleMiddleware(dummy_response)
        self.stdout.write(f"   Middleware request_limit: {middleware.request_limit}")
        self.stdout.write(f"   Middleware request_window: {middleware.request_window}")
        
        # Test with fake request
        factory = RequestFactory()
        request = factory.get('/')
        
        # Mock an anonymous user
        class MockUser:
            is_authenticated = False
            
        request.user = MockUser()
        
        self.stdout.write(f"\n🧪 Testing maybe_throttle:")
        result = middleware.maybe_throttle(request)
        self.stdout.write(f"   maybe_throttle() returned: {result}")
        
        if result is False:
            self.stdout.write(self.style.SUCCESS("✅ Request would NOT be throttled"))
        else:
            self.stdout.write(self.style.ERROR("❌ Request WOULD be throttled"))
            
        # Test IP address detection
        self.stdout.write(f"\n🌐 IP Address Detection:")
        self.stdout.write(f"   REMOTE_ADDR: {request.META.get('REMOTE_ADDR', 'NOT SET')}")
        self.stdout.write(f"   HTTP_X_FORWARDED_FOR: {request.META.get('HTTP_X_FORWARDED_FOR', 'NOT SET')}")
        self.stdout.write(f"   HTTP_X_REAL_IP: {request.META.get('HTTP_X_REAL_IP', 'NOT SET')}")
        
        # Check cache
        from django.core.cache import cache
        test_key = "throttle:global:127.0.0.1"
        cache_value = cache.get(test_key, "NOT FOUND")
        self.stdout.write(f"\n💾 Cache Test:")
        self.stdout.write(f"   Test cache key: {test_key}")
        self.stdout.write(f"   Current value: {cache_value}")
        
        # Test cache operations
        cache.set("test_throttle_cache", "working", 60)
        cache_test = cache.get("test_throttle_cache", "FAILED")
        self.stdout.write(f"   Cache write/read test: {cache_test}")
        
        # Check middleware list
        middleware_list = getattr(settings, "MIDDLEWARE", [])
        throttle_middleware = "global_throttle.middleware.GlobalThrottleMiddleware"
        
        self.stdout.write(f"\n📝 Middleware Configuration:")
        if throttle_middleware in middleware_list:
            index = middleware_list.index(throttle_middleware)
            self.stdout.write(f"   GlobalThrottleMiddleware is at position {index}")
            self.stdout.write(f"   Full middleware list:")
            for i, mw in enumerate(middleware_list):
                marker = " ← GlobalThrottleMiddleware" if mw == throttle_middleware else ""
                self.stdout.write(f"     {i}: {mw}{marker}")
        else:
            self.stdout.write(self.style.ERROR("   GlobalThrottleMiddleware NOT FOUND in MIDDLEWARE"))
            
        # Show a simulation of multiple requests
        self.stdout.write(f"\n🔄 Simulation (first 5 requests from same IP):")
        for i in range(5):
            result = middleware.maybe_throttle(request)
            self.stdout.write(f"   Request {i+1}: {'THROTTLED' if result else 'ALLOWED'}") 