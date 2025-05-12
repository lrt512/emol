"""URLs for the SSO user, supporting OAuth"""

from django.urls import path, re_path

from . import views

urlpatterns = [
    path("login", views.oauth_login, name="login"),
    path("logout", views.oauth_logout, name="logout"),
    path("callback", views.oauth_callback, name="oauth_callback"),
    re_path(r"^admin/oauth/$", views.admin_oauth, name="admin_oauth"),
]
