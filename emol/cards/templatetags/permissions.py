from django import template

from cards.models.user_permission import UserPermission
from current_user import get_current_user

register = template.Library()


@register.simple_tag
def has_global_permission(user, permission_slug):
    if not user.is_authenticated:
        return False

    return UserPermission.user_has_permission(user, permission_slug)


@register.simple_tag
def has_permission(user, permission_slug, discipline):
    if not user.is_authenticated:
        return False

    return UserPermission.user_has_permission(user, permission_slug, discipline)
