import logging

from django.contrib import messages
from django.contrib.auth import login, logout
from django.shortcuts import redirect
from django.urls import reverse
from django.views.decorators.cache import never_cache

from sso_user.google_oauth import GoogleOAuth
from sso_user.models import SSOUser

ADMIN_OAUTH_LOGIN_HINT = "admin-oauth-login-hint"

logger = logging.getLogger("cards")


@never_cache
def oauth_login(request):
    redirect_uri = request.build_absolute_uri(reverse("oauth_callback"))
    oauth = GoogleOAuth()
    return oauth.google.authorize_redirect(request, redirect_uri)


@never_cache
def oauth_callback(request):
    oauth = GoogleOAuth()
    token = oauth.google.authorize_access_token(request)

    userinfo = token.get("userinfo")
    if userinfo is None:
        raise ValueError("OAuth provider did not return userinfo")

    email = userinfo.get("email")
    if email is None:
        raise ValueError("OAuth provider did not return user email")

    try:
        user = SSOUser.objects.get(email=email)
        login(request, user)
    except SSOUser.DoesNotExist:
        logger.error("Unauthorized login attempt for %s", email)
    return redirect("/")


@never_cache
def oauth_logout(request):
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

    email = userinfo.get("email")
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
