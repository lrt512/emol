import logging

from cards.models.user_permission import UserPermission
from current_user import get_current_user
from django import template

logger = logging.getLogger("cards")
register = template.Library()


@register.simple_tag
def has_global_permission(user, permission_slug, override=None, reason=None):
    """Check a global permission.

    Args:
        user: The user to check the permission for
        permission_slug: The slug of the permission to check
        override: If True, the permission will be overridden by the extra permission

        Currently, override is only used for self-serve updates to allow
        combatants to update their own information.

    Returns:
        True if the user has the permission, False otherwise
    """
    if override:
        if not reason:
            logger.error(
                f"has_global_permission: {permission_slug} override: {override} but no reason provided"
            )
            return False

        logger.info(
            f"has_global_permission: {permission_slug} override: {override} reason: {reason}"
        )
        return override

    if not user.is_authenticated:
        return False

    permission = UserPermission.user_has_permission(user, permission_slug)
    return permission


@register.simple_tag
def has_permission(user, permission_slug, discipline):
    if not user.is_authenticated:
        return False

    return UserPermission.user_has_permission(user, permission_slug, discipline)
