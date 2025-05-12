from django.db import models

from current_user import get_current_user
from cards.models.permission import PermissionDenied


class PermissionEnforcedField(models.Field):
    def __init__(self, *args, **kwargs):
        self.permissions = kwargs.pop("permissions", [])
        super().__init__(*args, **kwargs)

    def has_permission(self, user, obj=None):
        if self.permissions:
            for permission in self.permissions:
                if not user.has_perm(permission, obj=obj):
                    return False
        return True

    def contribute_to_class(self, cls, name, **kwargs):
        super().contribute_to_class(cls, name, **kwargs)
        setattr(cls, f"_{name}_permissions", self.permissions)

    def __get__(self, instance, instance_type=None):
        if instance is None:
            return self

        user = get_current_user()
        if not self.has_permission(user, obj=instance):
            raise PermissionDenied("You do not have permission to view this field")

        return super().__get__(instance, instance_type)

    def __set__(self, instance, value):
        user = get_current_user()
        if not self.has_permission(user, obj=instance):
            raise PermissionDenied("You do not have permission to edit this field")

        super().__set__(instance, value)


class PermissionedCharField(PermissionEnforcedField, models.CharField):
    pass


class PermissionedDateField(PermissionEnforcedField, models.DateField):
    pass


class PermissionedIntegerField(PermissionEnforcedField, models.IntegerField):
    pass
