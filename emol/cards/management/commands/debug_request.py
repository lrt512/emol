"""Management command to debug HTTP request processing."""

from django.core.cache import cache
from django.core.management.base import BaseCommand
from django.test import Client


class Command(BaseCommand):
    """Debug HTTP request processing and throttling."""

    help = "Debug HTTP request processing and throttling"

    def add_arguments(self, parser):
        """Add command arguments."""
        parser.add_argument(
            "--clear-cache",
            action="store_true",
            help="Clear throttle cache before testing",
        )
        parser.add_argument(
            "--requests",
            type=int,
            default=5,
            help="Number of test requests to make (default: 5)",
        )

    def handle(self, *args, **options):
        """Execute the debug command."""
        self.stdout.write("🌐 Testing HTTP Requests and Throttling\n")

        if options["clear_cache"]:
            # Clear all throttle-related cache keys
            cache_keys = []
            try:
                # Try to get cache keys (if supported by backend)
                all_keys = (
                    cache._cache.keys("throttle:*")
                    if hasattr(cache._cache, "keys")
                    else []
                )
                for key in all_keys:
                    cache.delete(key)
                    cache_keys.append(key)
                self.stdout.write(f"🧹 Cleared {len(cache_keys)} throttle cache keys")
            except Exception as e:
                self.stdout.write(f"⚠️  Could not clear cache keys: {e}")
                # Try to clear some common ones
                for i in range(256):
                    for j in range(256):
                        for k in range(256):
                            key = f"throttle:global:{i}.{j}.{k}.1"
                            cache.delete(key)

        # Create test client
        client = Client()

        self.stdout.write(f"🧪 Making {options['requests']} test requests to /")

        responses = []
        for i in range(options["requests"]):
            response = client.get("/")
            status = response.status_code

            # Check for throttling headers or 429 status
            limit = response.get("X-RateLimit-Limit", "Not Set")
            remaining = response.get("X-RateLimit-Remaining", "Not Set")
            window = response.get("X-RateLimit-Window", "Not Set")

            self.stdout.write(f"  Request {i+1}: Status {status}")
            if status == 429:
                self.stdout.write(self.style.ERROR("    ❌ THROTTLED"))
            else:
                self.stdout.write(self.style.SUCCESS("    ✅ OK"))

            self.stdout.write(
                f"  Headers - Limit: {limit}, Remaining: {remaining}, Window: {window}"
            )

            responses.append(
                {
                    "status": status,
                    "limit": limit,
                    "remaining": remaining,
                    "window": window,
                }
            )

        # Summary
        throttled_count = sum(1 for r in responses if r["status"] == 429)
        self.stdout.write("\n📊 Summary:")
        self.stdout.write(f"   Total requests: {len(responses)}")
        self.stdout.write(f"   Successful: {len(responses) - throttled_count}")
        self.stdout.write(f"   Throttled: {throttled_count}")

        if throttled_count > 0:
            self.stdout.write(
                self.style.ERROR(f"\n❌ {throttled_count} requests were throttled")
            )
            self.stdout.write(
                "This suggests the throttling middleware is active and working"
            )
        else:
            self.stdout.write(self.style.SUCCESS("\n✅ No requests were throttled"))
            self.stdout.write("Either throttling is disabled or limit is not reached")

        # Check cache after requests
        self.stdout.write("\n💾 Cache check after requests:")
        test_keys = [
            "throttle:global:127.0.0.1",
            "throttle:global:localhost",
            "throttle:global:::1",
        ]

        for key in test_keys:
            value = cache.get(key, "Not Found")
            self.stdout.write(f"   {key}: {value}")
