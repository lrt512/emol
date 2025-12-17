import logging

from django.conf import settings
from django.core.exceptions import ValidationError
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
            return (
                f"<UserPermission: {self.user.email} - {self.permission.name} "
                f"({self.discipline.name})>"
            )
        else:
            return (
                f"<UserPermission: {self.user.email} - {self.permission.name} (global)>"
            )

    def clean(self):
        """Validate that global permissions don't have disciplines assigned"""
        super().clean()

        if (
            self.permission
            and self.permission.is_global
            and self.discipline is not None
        ):
            raise ValidationError(
                {
                    "discipline": (
                        f"Global permission '{self.permission.name}' "
                        "cannot be assigned to a specific discipline. Global "
                        "permissions must be discipline-independent."
                    ),
                }
            )

        if (
            self.permission
            and not self.permission.is_global
            and self.discipline is None
        ):
            raise ValidationError(
                {
                    "discipline": (
                        f"Non-global permission '{self.permission.name}' "
                        "requires a discipline to be specified."
                    ),
                }
            )

    def save(self, *args, **kwargs):
        """Override save to ensure validation is run"""
        self.full_clean()
        super().save(*args, **kwargs)

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
            logger.error("Permission '%s' does not exist", permission)
            return False

        filters = {
            "user": user,
            "permission": permission,
        }

        if permission.is_global:
            # Global permissions must have discipline=None
            # We don't consider the discipline parameter for global permissions
            filters["discipline"] = None
        else:
            # Non-global permissions require a specific discipline
            try:
                discipline = Discipline.find(discipline)
                filters["discipline"] = discipline
            except Discipline.DoesNotExist:
                logger.error("Discipline '%s' does not exist", discipline)
                return False

        return UserPermission.objects.filter(**filters).exists()
