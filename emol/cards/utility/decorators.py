# -*- coding: utf-8 -*-
"""Decorators for access control."""

from functools import wraps

from cards.models.user_permission import UserPermission
from current_user.middleware import get_current_user
from django.http import HttpResponse


def permission_required(permission, related=None):
    """Require that a user have a specific global permission.

    To use it, decorate your method like this::

        @permission_required('write_combatant_info')
        def get(self):
            ...

    """

    def actual_decorator(handler_method):
        """Extra nested function before the wrap.

        Necessary so that the permission parameter is available within scope

        """

        @wraps(handler_method)
        def check_permission(*args, **kwargs):
            """Perform the check."""
            current_user = get_current_user()
            if current_user is None:
                return HttpResponse(status=401)

            if not UserPermission.user_has_permission(
                current_user, permission, related
            ):
                return HttpResponse(status=401)

            return handler_method(*args, **kwargs)

        return check_permission

    return actual_decorator
