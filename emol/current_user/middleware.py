"""
On requests, stash the current user in thread local storage
if the user is not anonymous, for ease of reference through
models and code.

Shamelessly cribbed from https://github.com/PaesslerAG/django-currentuser

"""

from threading import local

from django.contrib.auth.models import AnonymousUser

USER_ATTR_NAME = "__current_user__"

_thread_locals = local()


def _set_current_user(user_func):
    # setattr(_thread_locals, USER_ATTR_NAME, user_func)
    # Maybe we don't need to make a bound method here
    setattr(
        _thread_locals,
        USER_ATTR_NAME,
        getattr(user_func, "__get__", lambda: user_func)(user_func, local),
    )


class ThreadLocalUserMiddleware:
    """Middleware to store current user in thread-local storage."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # request.user closure; asserts laziness;
        # memorization is implemented in
        # request.user (non-data descriptor)
        _set_current_user(lambda self: getattr(request, "user", None))
        response = self.get_response(request)
        return response


def get_current_user():
    """
    We won't use this directly from here.
    Let's import it into some utils in apps instead
    """
    current_user = getattr(_thread_locals, USER_ATTR_NAME, None)
    if isinstance(current_user, AnonymousUser):
        return None

    if callable(current_user):
        return current_user()  # type: ignore[misc,operator]

    return current_user
