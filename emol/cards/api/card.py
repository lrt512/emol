import logging

from django.shortcuts import get_object_or_404
from rest_framework import serializers, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.renderers import JSONRenderer
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet

from cards.models.card import Card
from cards.models.combatant_authorization import CombatantAuthorization
from cards.models.combatant_warrant import CombatantWarrant
from cards.models.discipline import Discipline

from .permissions import CardDatePermission

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

        # Retrieve card based on uuid and discipline_slug
        uuid = serializer.validated_data["uuid"]
        discipline_slug = serializer.validated_data["discipline_slug"]
        card = get_object_or_404(
            Card, combatant__uuid=uuid, discipline__slug=discipline_slug
        )

        # Update date_issued field
        card.date_issued = serializer.validated_data["date_issued"]
        card.save()

        return Response(status=status.HTTP_204_NO_CONTENT)
