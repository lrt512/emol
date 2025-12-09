"""Middleware to implement a global throttle for anonymous users"""

import logging

from django.conf import settings
from django.core.cache import cache
from django.shortcuts import render
from django.urls import resolve

logger = logging.getLogger("global_throttle")


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
        self.request_limit = getattr(settings, "GLOBAL_THROTTLE_LIMIT", None)
        self.request_window = getattr(settings, "GLOBAL_THROTTLE_WINDOW", None)

        if self.request_limit is None:
            logger.error(
                "GLOBAL_THROTTLE_LIMIT is not set, using default of 100 requests"
            )
            self.request_limit = 100

        if self.request_window is None:
            logger.error(
                "GLOBAL_THROTTLE_WINDOW is not set, using default of 3600 seconds"
            )
            self.request_window = 3600

        logger.debug(
            f"GlobalThrottleMiddleware initialized: limit={self.request_limit}, window={self.request_window}"
        )

        self.whitelist = getattr(
            settings, "GLOBAL_THROTTLE_WHITELIST", ["127.0.0.1", "localhost", "::1"]
        )

    def get_client_ip(self, request):
        """Get the real client IP address, considering proxy headers."""
        # Check for real IP from nginx proxy
        x_real_ip = request.META.get("HTTP_X_REAL_IP")
        if x_real_ip:
            return x_real_ip

        # Check X-Forwarded-For header (get first IP)
        x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
        if x_forwarded_for:
            # X-Forwarded-For can contain multiple IPs, get the first one
            return x_forwarded_for.split(",")[0].strip()

        # Fallback to REMOTE_ADDR
        return request.META.get("REMOTE_ADDR", "unknown")

    def maybe_throttle(self, request):
        """Determine if we should throttle the calling IP address"""
        if request.user.is_authenticated:
            logger.debug(
                f"User {request.user.email} is authenticated, skipping throttle"
            )
            return False

        ip_address = self.get_client_ip(request)

        if ip_address in self.whitelist:
            logger.debug(f"IP address {ip_address} is whitelisted, skipping throttle")
            return False

        view_func = resolve(request.path).func
        if getattr(view_func, "exempt_from_throttling", False):
            logger.debug(
                f"View function {view_func.__name__} is exempt from throttling, skipping throttle"
            )
            return False

        cache_key = f"throttle:global:{ip_address}"
        request_count = cache.get(cache_key, 0)

        request.throttle_remaining = max(0, self.request_limit - request_count)
        logger.debug(f"Request count {request_count} for IP address {ip_address}")

        if request_count >= self.request_limit:
            logger.error(
                f"THROTTLING: Request count {request_count} exceeds limit {self.request_limit} for {ip_address}"
            )
            return True

        cache.set(cache_key, request_count + 1, self.request_window)
        logger.debug(
            f"Request count {request_count + 1} for IP address {ip_address} after increment"
        )
        return False

    def __call__(self, request):
        """Handle the request and throttle if necessary"""
        logger.debug(f"GlobalThrottleMiddleware processing request to {request.path}")
        throttled = self.maybe_throttle(request)
        ip_address = self.get_client_ip(request)

        if throttled:
            logger.error(
                f"MIDDLEWARE THROTTLING: Returning 429 for {request.path} from IP {ip_address}"
            )
            response = render(request, "429.html", status=429)
        else:
            logger.debug(
                f"Request to {request.path} from IP {ip_address} allowed by middleware"
            )
            response = self.get_response(request)

        # response["X-RateLimit-Limit"] = str(self.request_limit)
        # response["X-RateLimit-Remaining"] = str(
        #     getattr(request, "throttle_remaining", 0)
        # )
        # response["X-RateLimit-Window"] = f"{self.request_window}s"

        return response
