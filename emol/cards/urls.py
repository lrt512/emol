# -*- coding: utf-8 -*-
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.admin import site
from django.urls import include, path
from django.views.generic import TemplateView

from cards.api.urls import urlpatterns as api_urlpatterns
from cards.views import combatant, home, privacy, self_serve_update

site.site_header = "Ealdormere eMoL"
site.site_title = "eMoL Admin"
site.index_title = "eMoL Admin"

urlpatterns = [
    path("", home.index, name="index"),
    path("request-card", home.request_card, name="request-card"),
    path("update-info", home.update_info, name="update-info"),
    path("marshal-list", home.marshal_list, name="marshal-list"),
    path(
        "self-serve-update/<str:code>",
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
    path("privacy-policy/<str:code>", privacy.privacy_policy, name="privacy-policy"),
    path("api/", include(api_urlpatterns)),
]

# Custom error handlers
urlpatterns += [
    path(
        "429/",
        TemplateView.as_view(template_name="429.html"),
        name="too_many_requests",
    ),
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
