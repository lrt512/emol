import logging

from cards.api.permissions import CombatantMarshalPermission
from cards.models.card import Card
from cards.models.combatant import Combatant
from cards.models.combatant_warrant import CombatantWarrant
from cards.models.discipline import Discipline
from cards.models.marshal import Marshal
from cards.utility.time import today
from django.shortcuts import get_object_or_404
from rest_framework import serializers, status
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet


class CombatantWarrantSerializer(serializers.ModelSerializer):
    class Meta:
        model = CombatantWarrant
        fields = ["card", "marshal", "uuid"]


logger = logging.getLogger("cards")


class CombatantWarrantViewSet(GenericViewSet):
    """
    API endpoint to add and remove warrants from a combatant card
    """

    lookup_field = "uuid"

    queryset = CombatantWarrant.objects.all()
    permission_classes = [CombatantMarshalPermission]

    def create(self, request, discipline):
        """
        Add a warrant to a combatant's card for a discipline
        If the card doesn't exist for the specified discipline, create one.

        POST data:
            uuid - Combatant UUID
            discipline - A discipline slug
            marshal - A marshal slug
        """
        data = request.data
        uuid = data.get("combatant_uuid")
        discipline_slug = data.get("discipline")
        marshal_slug = data.get("marshal")

        logger.debug(
            "Add warrant %s/%s card for combatant %s",
            discipline_slug,
            marshal_slug,
            uuid,
        )

        combatant = get_object_or_404(Combatant, uuid=uuid)
        discipline = get_object_or_404(Discipline, slug=discipline_slug)
        marshal = get_object_or_404(
            Marshal.objects.filter(discipline=discipline), slug=marshal_slug
        )

        card, _created = Card.objects.get_or_create(
            combatant=combatant,
            discipline=discipline,
            defaults={"date_issued": today()},
        )

        serializer = CombatantWarrantSerializer(
            data={"card": card.id, "marshal": marshal.id}
        )
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        serializer.save()
        return Response(status=status.HTTP_200_OK, data=serializer.data)

    def destroy(self, request, uuid, *args, **kwargs):
        """
        Deletes the given CombatantWarrant
        If the related card has no more warrants or authorizations left, delete that too
        """
        try:
            instance = CombatantWarrant.objects.get(uuid=uuid)
        except CombatantWarrant.DoesNotExist:
            return Response(
                f"No such combatant-warrant {uuid}", status=status.HTTP_404_NOT_FOUND
            )

        logger.debug("Removing combatant-warrant %s", uuid)

        card = instance.card
        instance.delete()

        if card.warrants.count() == 0 and card.authorizations.count() == 0:
            logger.debug(
                "Card has no more authorizations or warrants attached, removing card"
            )
            card.delete()

        return Response(status=status.HTTP_204_NO_CONTENT)
