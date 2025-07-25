"""URLs for the SSO user, supporting OAuth"""

import os
from django.conf import settings
from django.urls import path, re_path

from . import views

urlpatterns = [
    path("login", views.oauth_login, name="login"),
    path("logout", views.oauth_logout, name="logout"),
    path("callback", views.oauth_callback, name="oauth_callback"),
    re_path(r"^admin/oauth/$", views.admin_oauth, name="admin_oauth"),
]

# Include mock OAuth callback in development or testing environments
if settings.DEBUG is True or os.getenv("EMOL_DEV") == "1":
    urlpatterns.append(
        path(
            "mock_oauth_callback/",
            views.mock_oauth_callback,
            name="mock_oauth_callback",
        )
    )
