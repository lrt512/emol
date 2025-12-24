"""Helper functions for checking feature switch status."""

import logging
from typing import Optional

from cards.models.combatant import Combatant
from django.core.cache import cache
from feature_switches.models import (
    ACCESS_MODE_DISABLED,
    ACCESS_MODE_GLOBAL,
    FeatureSwitch,
)

logger = logging.getLogger(__name__)

CACHE_KEY_PREFIX = "feature_switch:"
CACHE_TIMEOUT = 60


def is_enabled(switch_name: str, default: bool = False, user=None) -> bool:
    """Check if a feature switch is enabled for a user.

    Uses Django's cache framework for performance. Falls back to database
    lookup on cache miss.

    Args:
        switch_name: The unique name of the switch to check
        default: Value to return if switch doesn't exist (default: False)
        user: Optional user or combatant object to check access for.
              Required for 'list' mode. If a User (SSOUser) is passed,
              will look up Combatant by email.

    Returns:
        True if the switch exists and is enabled for the user, False otherwise
    """
    user_email = user.email if user and hasattr(user, "email") else None
    cache_key = f"{CACHE_KEY_PREFIX}{switch_name}"
    if user_email:
        cache_key = f"{cache_key}:{user_email}"

    cached_value = cache.get(cache_key)
    if cached_value is not None:
        if isinstance(cached_value, bool):
            logger.debug("cached feature switch %s is %s for %s", switch_name, cached_value, user_email)
            return cached_value
        return bool(cached_value)

    try:
        switch: FeatureSwitch = FeatureSwitch.objects.prefetch_related(
            "allowed_users"
        ).get(name=switch_name)

        if switch.access_mode == ACCESS_MODE_DISABLED:
            value = False
        elif switch.access_mode == ACCESS_MODE_GLOBAL:
            value = True
        elif switch.access_mode == "list":
            if user is None:
                value = False
            elif not switch.allowed_users.exists():
                value = False
            else:
                combatant: Optional[Combatant] = None
                if isinstance(user, Combatant):
                    combatant = user
                else:
                    combatant = Combatant.objects.filter(email=user_email).first()

                if combatant is None:
                    value = False
                else:
                    value = switch.allowed_users.filter(pk=combatant.pk).exists()
        else:
            logger.warning(
                "Unknown access_mode '%s' for switch '%s', defaulting to False",
                switch.access_mode,
                switch_name,
            )
            value = False

    except FeatureSwitch.DoesNotExist:
        logger.warning(
            "Feature switch '%s' does not exist, using default='%s'",
            switch_name,
            default,
        )
        value = bool(default)

    logger.debug("setting feature switch %s to %s for %s", switch_name, value, user_email)
    cache.set(cache_key, value, CACHE_TIMEOUT)
    return value


def clear_cache(switch_name: Optional[str] = None) -> None:
    """Clear the cache for feature switches.

    Clears both global and combatant-specific cache entries for the switch.
    Iterates through allowed_combatants to clear their email-based cache keys.

    Args:
        switch_name: If provided, clear only this switch's cache.
                     If None, clear all feature switch cache entries.
    """
    switch: FeatureSwitch
    if switch_name:
        base_cache_key = f"{CACHE_KEY_PREFIX}{switch_name}"
        cache.delete(base_cache_key)

        try:
            switch = FeatureSwitch.objects.prefetch_related("allowed_users").get(
                name=switch_name
            )
            for combatant in switch.allowed_users.all():
                combatant_cache_key = f"{base_cache_key}:{combatant.email}"
                cache.delete(combatant_cache_key)
        except FeatureSwitch.DoesNotExist:
            pass
    else:
        for switch in FeatureSwitch.objects.prefetch_related("allowed_users").all():
            base_cache_key = f"{CACHE_KEY_PREFIX}{switch.name}"
            cache.delete(base_cache_key)

            for combatant in switch.allowed_users.all():
                combatant_cache_key = f"{base_cache_key}:{combatant.email}"
                cache.delete(combatant_cache_key)
