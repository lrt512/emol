import logging
import os

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import login, logout
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect
from django.urls import reverse
from django.views import View
from django.views.decorators.cache import never_cache
from sso_user.google_oauth import GoogleOAuth
from sso_user.models import SSOUser

ADMIN_OAUTH_LOGIN_HINT = "admin-oauth-login-hint"

logger = logging.getLogger("cards")

oauth = GoogleOAuth()


@never_cache
def oauth_login(request: HttpRequest) -> HttpResponse:
    """Start OAuth flow."""
    redirect_uri = request.build_absolute_uri(reverse("oauth_callback"))
    return oauth.google.authorize_redirect(request, redirect_uri)


@never_cache
def oauth_callback(request):
    oauth = GoogleOAuth()
    token = oauth.google.authorize_access_token(request)

    userinfo = token.get("userinfo")
    print(userinfo)
    if userinfo is None:
        raise ValueError("OAuth provider did not return userinfo")

    email = userinfo.get("email") or userinfo.get("sub")
    if email is None:
        raise ValueError("OAuth provider did not return user email")

    try:
        user = SSOUser.objects.get(email=email)
        login(request, user)
    except SSOUser.DoesNotExist:
        logger.error("Unauthorized login attempt for %s", email)
    return redirect("/")


@never_cache
def oauth_logout(request: HttpRequest) -> HttpResponse:
    """Log out and return to home page."""
    logout(request)
    return redirect("/")


@never_cache
def admin_oauth(request):
    oauth = GoogleOAuth()

    if all(key not in request.GET for key in ("code", "oauth_token")):
        redirect_uri = request.build_absolute_uri(reverse("admin_oauth"))
        return oauth.google.authorize_redirect(request, redirect_uri)

    token = oauth.google.authorize_access_token(request)

    userinfo = token.get("userinfo")
    if userinfo is None:
        messages.error(request, "OAuth provider did not return userinfo")
        return redirect("admin:login")

    email = userinfo.get("email") or userinfo.get("sub")
    if email is None:
        messages.error(request, "OAuth provider did not return user email")
        response = redirect("admin:login")

    try:
        user = SSOUser.objects.get(email=email)
        if user.is_superuser:
            login(request, user)
            response = redirect("admin:index")
            response.set_cookie(ADMIN_OAUTH_LOGIN_HINT, email, expires=30 * 86400)
            return response
    except SSOUser.DoesNotExist:
        messages.error(request, f"Unauthorized login {email}")

    response = redirect("admin:login")
    response.delete_cookie(ADMIN_OAUTH_LOGIN_HINT)
    return response


class GoogleLoginView(View):
    def get(self, request: HttpRequest, *args: list, **kwargs: dict) -> HttpResponse:
        redirect_uri = request.build_absolute_uri(reverse("google_auth"))
        return oauth.google.authorize_redirect(request, redirect_uri)


class GoogleAuthorize(View):
    def get(self, request: HttpRequest, *args: list, **kwargs: dict) -> HttpResponse:
        token = oauth.google.fetch_token(request)
        request.session["google_token"] = token
        user_info = oauth.google.userinfo(token)
        request.session["user_info"] = user_info
        assert settings.LOGIN_REDIRECT_URL is not None
        return redirect(settings.LOGIN_REDIRECT_URL)


def logout_view(request: HttpRequest) -> HttpResponse:
    request.session.clear()
    assert settings.LOGOUT_REDIRECT_URL is not None
    return redirect(settings.LOGOUT_REDIRECT_URL)


@never_cache
def mock_oauth_callback(request: HttpRequest) -> HttpResponse:
    """Mock OAuth callback that creates/logs in development user."""
    if os.getenv("EMOL_DEV") != "1":
        return HttpResponse("Mock OAuth only available in development", status=400)

    # Get mock token with userinfo
    token = oauth.google.authorize_access_token(request)
    userinfo = token["userinfo"]

    # Get or create user
    user, created = SSOUser.objects.get_or_create(
        email=userinfo["email"],
        defaults={
            "is_superuser": settings.MOCK_OAUTH_USER["is_superuser"],
            "is_staff": settings.MOCK_OAUTH_USER["is_staff"],
        },
    )

    # Log the user in
    login(request, user)

    # Store userinfo in session
    request.session["user_info"] = userinfo

    return redirect("/")
