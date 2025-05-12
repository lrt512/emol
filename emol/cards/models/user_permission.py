import logging

from django.conf import settings
from django.db import models

from sso_user.models import SSOUser

from .discipline import Discipline
from .permission import Permission

logger = logging.getLogger("cards")


class UserPermission(models.Model):
    user = models.ForeignKey(
        SSOUser, on_delete=models.CASCADE, related_name="user_permissions"
    )
    permission = models.ForeignKey(
        Permission, on_delete=models.CASCADE, related_name="user_permissionas"
    )
    discipline = models.ForeignKey(
        Discipline, on_delete=models.CASCADE, null=True, blank=True
    )

    class Meta:
        unique_together = ("user", "permission", "discipline")

    def __str__(self):
        if self.discipline:
            return f"<UserPermission: {self.user.email} - {self.permission.name} ({self.discipline.name})>"
        else:
            return (
                f"<UserPermission: {self.user.email} - {self.permission.name} (global)>"
            )

    @classmethod
    def user_has_permission(cls, user, permission, discipline=None):
        """Check if the given user has a permission

        Args:
            user: The user to check
            permission: The permission to check
            discipline: Discipline reference for non-global permissions
        """
        if not user or not user.is_authenticated:
            return False

        if getattr(settings, "NO_ENFORCE_PERMISSIONS", False):
            return True

        try:
            permission = Permission.find(permission)
        except Permission.DoesNotExist:
            logger.error(f"Permission '%s' does not exist", permission)
            return False

        filters = {
            "user": user,
            "permission": permission,
        }

        if not permission.is_global:
            try:
                discipline = Discipline.find(discipline)
                filters["discipline"] = discipline
            except Discipline.DoesNotExist:
                logger.error("Discipline '%s' does not exist", discipline)
                return False

        return UserPermission.objects.filter(**filters).exists()
