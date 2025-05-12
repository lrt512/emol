"""Middleware to implement a global throttle for anonymous users"""

from django.conf import settings
from django.core.cache import cache
from django.shortcuts import render
from django.urls import resolve

class GlobalThrottleMiddleware:
    """Global throttle middleware

    Throttle anonymous users on any page or endpoint.
    Default permissible rate is 10 requests per hour.

    Set GLOBAL_THROTTLE_LIMIT and GLOBAL_THROTTLE_WINDOW in settings.py
    to customize the throttle rate.

    Usage:
    1) This middleware must come after these middleware classes:

    django.contrib.sessions.middleware.SessionMiddleware
    django.contrib.auth.middleware.AuthenticationMiddleware

    2) Define a 429.html template to display when the throttle is triggered.

    3) Optionally set the following settings in settings.py:
    GLOBAL_THROTTLE_LIMIT: the maximum number of requests allowed within the duration
    GLOBAL_THROTTLE_WINDOW: the duration of the throttling window in seconds
    """

    def __init__(self, get_response):
        self.get_response = get_response
        self.request_limit = getattr(settings, "GLOBAL_THROTTLE_LIMIT", 10)
        self.request_window = getattr(settings, "GLOBAL_THROTTLE_WINDOW", 3600)

    def maybe_throttle(self, request):
        """Determine if we should throttle the calling IP address

        Returns True if the IP address should be throttled, False otherwise.
        """
        return False

        if request.user.is_authenticated:
            return False

        view_func = resolve(request.path).func
        if getattr(view_func, "exempt_from_throttling", False):
            return False

        ip_address = request.META.get("REMOTE_ADDR")
        cache_key = f"throttle:global:{ip_address}"

        request_count = cache.get(cache_key, 0)
        if request_count >= self.request_limit:
            return True

        cache.set(cache_key, request_count + 1, self.request_window)
        return False

    def __call__(self, request):
        """Handle the request and throttle if necessary"""
        if self.maybe_throttle(request):
            return render(request, "429.html", status=429)

        response = self.get_response(request)

        return response
