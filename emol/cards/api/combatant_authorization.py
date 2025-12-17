import logging

from cards.api.permissions import CombatantAuthorizationPermission
from cards.models import (
    Authorization,
    Card,
    Combatant,
    CombatantAuthorization,
    Discipline,
)
from cards.utility.time import today
from django.shortcuts import get_object_or_404
from rest_framework import serializers, status
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet

logger = logging.getLogger("cards")


class CombatantAuthorizationSerializer(serializers.ModelSerializer):
    """Serializer for CombatantAuthorization model"""

    class Meta:
        model = CombatantAuthorization
        fields = ["card", "authorization", "uuid"]


class CombatantAuthorizationViewSet(GenericViewSet):
    """
    API viewset to add and remove auths from a combatant card
    """

    lookup_field = "uuid"

    queryset = CombatantAuthorization.objects.all()
    permission_classes = [CombatantAuthorizationPermission]

    def create(self, request, discipline):
        """
        Add an authorization to a combatant's card for a discipline
        If the card doesn't exist for the specified discipline, create one.

        POST data:
            combatant_uuid - Combatant UUID
            discipline - A discipline slug
            authorization - An authorization slug
        """
        data = request.data
        uuid = data.get("combatant_uuid")
        discipline_slug = data.get("discipline")
        authorization_slug = data.get("authorization")

        logger.debug(
            "Add authorization %s/%s card for combatant %s",
            discipline_slug,
            authorization_slug,
            uuid,
        )

        combatant = get_object_or_404(Combatant, uuid=uuid)
        discipline = get_object_or_404(Discipline, slug=discipline_slug)
        authorization = get_object_or_404(
            Authorization.objects.filter(discipline=discipline),
            slug=authorization_slug,
        )

        card, created = Card.objects.get_or_create(
            combatant=combatant,
            discipline=discipline,
            defaults={"date_issued": today()},
        )

        logger.debug("Create combatant-authorization record")
        serializer = CombatantAuthorizationSerializer(
            data={"card": card.id, "authorization": authorization.id}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(status=status.HTTP_200_OK, data=serializer.data)

    def destroy(self, request, *args, **kwargs):
        """
        Delete the given CombatantAuthorization
        If the related card has no authorizations left, delete that too
        """
        instance = get_object_or_404(CombatantAuthorization, uuid=kwargs["uuid"])

        logger.debug("Remove combatant-authorization %s", kwargs["uuid"])
        card = instance.card
        instance.delete()

        if card.authorizations.count() == 0 and card.warrants.count() == 0:
            logger.debug(
                "Card has no more authorizations or warrants attached, removing card"
            )
            card.delete()

        return Response(status=status.HTTP_204_NO_CONTENT)
