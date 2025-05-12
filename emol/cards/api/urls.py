from django.urls import include, path, re_path
from rest_framework import routers

from .card import CardDateViewSet, CardViewSet
from .combatant import CombatantListViewSet, CombatantViewSet
from .combatant_authorization import CombatantAuthorizationViewSet
from .combatant_warrant import CombatantWarrantViewSet
from .privacy import ResendPrivacyView
from .waiver import WaiverViewSet

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

# We have some non-model API views, so let's create urlpatterns manaully
urlpatterns = [
    path("", include(api_router.urls)),
    re_path(r"^resend-privacy/$", ResendPrivacyView.as_view(), name="resend-privacy"),
]
