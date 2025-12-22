from cards.api.card import CardDateViewSet, CardViewSet
from cards.api.combatant import CombatantListViewSet, CombatantViewSet
from cards.api.combatant_authorization import CombatantAuthorizationViewSet
from cards.api.combatant_warrant import CombatantWarrantViewSet
from cards.api.pin import InitiatePinResetView
from cards.api.privacy import ResendPrivacyView
from cards.api.waiver import WaiverViewSet
from django.urls import include, path, re_path
from rest_framework import routers

api_router = routers.SimpleRouter()
api_router.register(r"combatant-list", CombatantListViewSet, basename="combatant-list")
api_router.register(r"combatant", CombatantViewSet, basename="combatant")
api_router.register(
    r"combatant-authorization/(?P<discipline>[-\w]+)",
    CombatantAuthorizationViewSet,
    basename="combatant-authorization",
)
api_router.register(
    r"combatant-warrant/(?P<discipline>[-\w]+)",
    CombatantWarrantViewSet,
    basename="combatant-warrant",
)
api_router.register(r"combatant-cards", CardViewSet, basename="combatant-cards")
api_router.register(r"waiver", WaiverViewSet, basename="waiver")

api_router.register(r"card-date", CardDateViewSet, basename="card-date")

urlpatterns = [
    path("", include(api_router.urls)),
    re_path(r"^resend-privacy/$", ResendPrivacyView.as_view(), name="resend-privacy"),
    re_path(
        r"^initiate-pin-reset/$",
        InitiatePinResetView.as_view(),
        name="initiate-pin-reset",
    ),
]
