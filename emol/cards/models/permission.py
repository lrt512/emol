# -*- coding: utf-8 -*-
"""Model permissions for access control."""
from django.db import models
from django.utils.text import slugify

__all__ = ["Permission"]


class PermissionDenied(Exception):
    """Custom permission denied exception"""


class Permission(models.Model):
    """Model a permission.

    Roles are assigned to users to indicate what actions they are permitted
    to perform. The UserRole class represents
    an association table matching Users to Roles.

    Attributes:
        id: Primary key in the database
        name: Readable name for the permission
        slug: A tokenized version of the name friendly to database and URL
        is_global: Indicates whether the permission is global or discipline-specific
        discipline: If not None, the discipline associated with the permission

    """

    # Minimum permissions set
    DEFAULT_PERMISSIONS = [
        {
            "name": "Can read combatant info",
            "slug": "read_combatant_info",
            "is_global": True,
        },
        {
            "name": "Can write combatant info",
            "slug": "write_combatant_info",
            "is_global": True,
        },
        {
            "name": "Can write waiver dates",
            "slug": "write_waiver_date",
            "is_global": True,
        },
        {"name": "Can edit card dates", "slug": "write_card_date", "is_global": False},
        {
            "name": "Can write authorizations",
            "slug": "write_authorizations",
            "is_global": False,
        },
        {
            "name": "Can write marshal status",
            "slug": "write_marshal",
            "is_global": False,
        },
        {
            "name": "Can generate warrant roster",
            "slug": "warrant_roster",
            "is_global": False,
        },
        {"name": "Can import combatants", "slug": "can_import", "is_global": False},
        {
            "name": "Can write kingdom officers",
            "slug": "write_officer_info",
            "is_global": False,
        },
        {
            "name": "Can initiate PIN reset",
            "slug": "can_initiate_pin_reset",
            "is_global": True,
        },
        {
            "name": "Can edit privacy policy",
            "slug": "can_edit_privacy_policy",
            "is_global": True,
        },
    ]

    # Roles associated with editing combatants.
    # Used by User.can_see_combatant_list
    COMBATANT_EDIT_PERMISSIONS = (
        "read_combatant_info",
        "write_combatant_info",
        "write_card_date",
        "write_authorizations",
        "write_marshal",
    )

    # These permissions are always global
    GLOBAL_PERMISSIONS = [
        "read_combatant_info",
        "write_combatant_info",
        "write_waiver_date",
        "can_initiate_pin_reset",
        "can_edit_privacy_policy",
    ]

    slug = models.CharField(max_length=255, null=False)
    name = models.CharField(max_length=255, null=False)
    is_global = models.BooleanField(default=False)
    is_default = models.BooleanField(default=False)

    def __str__(self):
        return f"<Permission: {self.name}>"

    def save(self, *args, **kwargs):
        if not self.pk and not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    @classmethod
    def find(cls, permission):
        """Look up a permission.

        Args:
            permission: A permission slug or ID (or maybe a Role object)

        Returns:
            Role object

        Raises:
            ValueError if discipline can't be determined

        """
        #  Null cases
        if permission is None:
            return None

        if isinstance(permission, Permission):
            return permission

        if isinstance(permission, str):
            query = models.Q(slug=permission) | models.Q(name=permission)
            return Permission.objects.get(query)

        if isinstance(permission, int):
            return Permission.objects.get(id=permission)

        raise Permission.DoesNotExist()
