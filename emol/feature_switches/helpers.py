"""Helper functions for checking feature switch status."""

import logging
from functools import lru_cache
from typing import Optional

from django.core.cache import cache

logger = logging.getLogger(__name__)

CACHE_KEY_PREFIX = "feature_switch:"
CACHE_TIMEOUT = 60


def is_enabled(switch_name: str, default: bool = False) -> bool:
    """Check if a feature switch is enabled.

    Uses Django's cache framework for performance. Falls back to database
    lookup on cache miss.

    Args:
        switch_name: The unique name of the switch to check
        default: Value to return if switch doesn't exist (default: False)

    Returns:
        True if the switch exists and is enabled, False otherwise
    """
    cache_key = f"{CACHE_KEY_PREFIX}{switch_name}"

    cached_value = cache.get(cache_key)
    if cached_value is not None:
        return cached_value

    from .models import FeatureSwitch

    try:
        switch = FeatureSwitch.objects.get(name=switch_name)
        value = switch.enabled
    except FeatureSwitch.DoesNotExist:
        logger.warning(
            f"Feature switch '{switch_name}' does not exist, using default={default}"
        )
        value = default

    cache.set(cache_key, value, CACHE_TIMEOUT)
    return value


def clear_cache(switch_name: Optional[str] = None) -> None:
    """Clear the cache for feature switches.

    Args:
        switch_name: If provided, clear only this switch's cache.
                     If None, clear all feature switch cache entries.
    """
    if switch_name:
        cache_key = f"{CACHE_KEY_PREFIX}{switch_name}"
        cache.delete(cache_key)
    else:
        from .models import FeatureSwitch

        for switch in FeatureSwitch.objects.all():
            cache_key = f"{CACHE_KEY_PREFIX}{switch.name}"
            cache.delete(cache_key)
