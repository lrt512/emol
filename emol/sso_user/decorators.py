# -*- coding: utf-8 -*-
"""Decorators for access control."""

from functools import wraps

from django.http import HttpResponse, HttpResponseRedirect
from django.urls import reverse

from current_user.middleware import get_current_user

from . import views


def login_required(handler_method):
    """Require that a user be logged in.

    To use it, decorate your method like this:

        @login_required
        def get(self):
            ...
    """

    @wraps(handler_method)
    def check_login(*args, **kwargs):
        """Perform the check."""
        if not get_current_user():
            # Short-circuit anonymous API invocations
            if "emol.api" in args[0].__module__:
                return HttpResponse(401)

            return HttpResponseRedirect(reverse(views.oauth_login))

        return handler_method(*args, **kwargs)

    return check_login


def admin_required(handler_method):
    """Require that a user be an admin.

    To use it, decorate your method like this::

        @admin_required
        def get(self):
            ...

    """

    @wraps(handler_method)
    def check_admin(*args, **kwargs):
        """Perform the check."""
        user = get_current_user()
        if user is None:
            return HttpResponse(401)

        if user.is_admin:
            return handler_method(*args, **kwargs)

        return HttpResponse(401)

    return check_admin
