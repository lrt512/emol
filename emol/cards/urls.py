# -*- coding: utf-8 -*-
from cards.api.urls import urlpatterns as api_urlpatterns
from cards.views import combatant, home, privacy
from django.contrib.admin import site
from django.urls import include, path
from django.conf import settings

site.site_header = "Ealdormere eMoL"
site.site_title = "eMoL Admin"
site.index_title = "eMoL Admin"

urlpatterns = [
    path("", home.index, name="index"),
    path("request-card", home.request_card, name="request-card"),
    path("update-info", home.update_info, name="update-info"),
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

if settings.DEBUG:
    from django.conf.urls.static import static

    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
