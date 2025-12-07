"""Proxy UserPermission checks as DRF permissions"""

from cards.models.user_permission import UserPermission
from rest_framework import permissions


class CombatantInfoPermission(permissions.BasePermission):
    """Check if user can read or write combatant info"""

    READ_PERMISSION = "read_combatant_info"
    WRITE_PERMISSION = "write_combatant_info"

    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return UserPermission.user_has_permission(
                request.user, self.READ_PERMISSION
            )

        return UserPermission.user_has_permission(
            request.user, self.WRITE_PERMISSION
        )

    def has_object_permission(self, request, view, obj):
        return self.has_permission(request, view)


class CombatantAuthorizationPermission(permissions.BasePermission):
    """Check if user can read or write combatant authorizations"""

    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True

        discipline_slug = view.kwargs.get("discipline")
        if not discipline_slug:
            return False

        return UserPermission.user_has_permission(
            request.user,
            CombatantAuthorizationPermission.WRITE_PERMISSION,
            discipline_slug,
        )

    WRITE_PERMISSION = "write_authorizations"


class CombatantMarshalPermission(permissions.BasePermission):
    """Check if user can read or write combatant warrants"""

    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True

        discipline_slug = view.kwargs.get("discipline")
        if not discipline_slug:
            return False

        return UserPermission.user_has_permission(
            request.user, CombatantMarshalPermission.WRITE_PERMISSION, discipline_slug
        )

    WRITE_PERMISSION = "write_marshal"


class WaiverDatePermission(permissions.BasePermission):
    """Check if user can read or write waiver date"""

    def has_permission(self, request, view):
        return UserPermission.user_has_permission(
            request.user, WaiverDatePermission.WRITE_PERMISSION
        )

    WRITE_PERMISSION = "write_waiver_date"


class CardDatePermission(permissions.BasePermission):
    """Check if user can write card date"""

    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return UserPermission.user_has_permission(
                request.user, CardDatePermission.WRITE_PERMISSION
            )

        data = request.data
        discipline_slug = data.get("discipline_slug")
        if not discipline_slug:
            return False
        return UserPermission.user_has_permission(
            request.user, CardDatePermission.WRITE_PERMISSION, discipline_slug
        )

    WRITE_PERMISSION = "write_card_date"


class ResendPrivacyPermission(permissions.BasePermission):
    """Allow resending privacy policy email for users who can read combatant info"""

    def has_permission(self, request, view):
        return UserPermission.user_has_permission(
            request.user, CombatantInfoPermission.READ_PERMISSION
        )
