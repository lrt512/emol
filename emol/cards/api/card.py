import logging

from cards.api.permissions import CardDatePermission
from cards.models.card import Card
from cards.models.combatant import Combatant
from cards.models.combatant_authorization import CombatantAuthorization
from cards.models.combatant_warrant import CombatantWarrant
from cards.models.discipline import Discipline
from django.shortcuts import get_object_or_404
from rest_framework import serializers, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.renderers import JSONRenderer
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet

logger = logging.getLogger("cards")


class CombatantAuthorizationSerializer(serializers.ModelSerializer):
    slug = serializers.SlugField(source="authorization.slug")
    name = serializers.CharField(source="authorization.name")

    class Meta:
        model = CombatantAuthorization
        fields = ["uuid", "slug", "name"]


class CombatantWarrantSerializer(serializers.ModelSerializer):
    slug = serializers.SlugField(source="marshal.slug")
    name = serializers.CharField(source="marshal.name")

    class Meta:
        model = CombatantWarrant
        fields = ["uuid", "slug", "name"]


class DisciplineSerializer(serializers.ModelSerializer):
    """Serializer for CombatantAuthorization model"""

    class Meta:
        model = Discipline
        fields = ["name", "slug"]


class CardSerializer(serializers.ModelSerializer):
    """Serializer for Card model"""

    authorizations = CombatantAuthorizationSerializer(
        source="combatantauthorization_set", many=True
    )
    warrants = CombatantWarrantSerializer(source="combatantwarrant_set", many=True)
    discipline = DisciplineSerializer(read_only=True)

    class Meta:
        model = Card
        fields = ["uuid", "discipline", "date_issued", "authorizations", "warrants"]


class CardViewSet(GenericViewSet):
    """
    API viewset that retrieves card data for combatants
    """

    queryset = Card.objects.all()
    serializer_class = CardSerializer
    renderer_classes = [JSONRenderer]
    permission_classes = [IsAuthenticated]
    lookup_field = "uuid"

    def retrieve(self, request, uuid):
        """
        Handle GET requests

        params:
            uuid - A combatant's UUID
        """
        cards = Card.objects.filter(combatant__uuid=uuid)
        serializer = self.get_serializer(cards, many=True)
        return Response(status=status.HTTP_200_OK, data=serializer.data)


class CardDateSerializer(serializers.Serializer):
    """Serializer for card issue date updates"""

    uuid = serializers.UUIDField()
    discipline_slug = serializers.CharField()
    date_issued = serializers.DateField()

    # We never try to save anything but in case we do someday, we have not
    # implemented these methods.
    def create(self, validated_data):
        raise NotImplementedError("This serializer is read-only")

    def update(self, instance, validated_data):
        raise NotImplementedError("This serializer is read-only")


class CardDateViewSet(GenericViewSet):
    """
    API viewset to update card issue date
    """

    queryset = Card.objects.all()
    permission_classes = [CardDatePermission]
    serializer_class = CardDateSerializer
    renderer_classes = [JSONRenderer]

    def update(self, request, **kwargs):
        """PUT endpoint to update card issue date"""
        serializer = self.get_serializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)

        uuid = serializer.validated_data["uuid"]
        discipline_slug = serializer.validated_data["discipline_slug"]
        date_issued = serializer.validated_data["date_issued"]

        combatant = get_object_or_404(Combatant, uuid=uuid)
        discipline = get_object_or_404(Discipline, slug=discipline_slug)

        Card.objects.update_or_create(
            combatant=combatant,
            discipline=discipline,
            defaults={"date_issued": date_issued},
        )

        return Response(status=status.HTTP_204_NO_CONTENT)
