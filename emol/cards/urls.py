# -*- coding: utf-8 -*-
from cards.api.urls import urlpatterns as api_urlpatterns
from cards.views import combatant, home, pin, privacy, self_serve_update
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.admin import site
from django.urls import include, path, re_path
from django.views.generic import TemplateView

site.site_header = "Ealdormere eMoL"
site.site_title = "eMoL Admin"
site.index_title = "eMoL Admin"

urlpatterns = [
    path("", home.index, name="index"),
    path("request-card", home.request_card, name="request-card"),
    path("update-info", home.update_info, name="update-info"),
    path("marshal-list", home.marshal_list, name="marshal-list"),
    re_path(
        r"^self-serve-update/(?P<code>[a-zA-Z0-9-]+)$",
        self_serve_update.self_serve_update,
        name="self-serve-update",
    ),
    path("combatants", combatant.combatant_list, name="combatant-list"),
    path("card/<str:card_id>", combatant.combatant_card, name="combatant-card"),
    path(
        "combatant-detail",
        combatant.combatant_detail,
        name="combatant-detail",
    ),
    path("privacy-policy", privacy.privacy_policy, name="privacy-policy"),
    path(
        "privacy-policy/edit",
        privacy.edit_privacy_policy,
        name="edit-privacy-policy",
    ),
    path(
        "privacy-policy/draft/<uuid:draft_uuid>",
        privacy.view_draft,
        name="view-draft",
    ),
    path(
        "privacy-policy/approve/<uuid:draft_uuid>",
        privacy.approve_policy,
        name="approve-policy",
    ),
    path(
        "privacy-policy/version/<str:version>",
        privacy.view_version,
        name="view-version",
    ),
    path("privacy-policy/<str:code>", privacy.privacy_policy, name="privacy-policy"),
    # PIN authentication URLs
    re_path(
        r"^pin/setup/(?P<code>[a-zA-Z0-9-]+)$",
        pin.pin_setup,
        name="pin-setup",
    ),
    re_path(
        r"^pin/reset/(?P<code>[a-zA-Z0-9-]+)$",
        pin.pin_reset,
        name="pin-reset",
    ),
    path("pin/verify/<str:card_id>", pin.pin_verify, name="pin-verify"),
    path("api/", include(api_urlpatterns)),  # type: ignore[arg-type]
]

# Custom error handlers
urlpatterns += [
    path(
        "404/",
        TemplateView.as_view(template_name="404.html"),
        name="not_found",
    ),
    path(
        "robots.txt",
        TemplateView.as_view(template_name="robots.txt", content_type="text/plain"),
        name="not_found",
    ),
]

urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
