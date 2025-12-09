import logging

from cards.models import Combatant, Region
from rest_framework import serializers
from rest_framework.renderers import JSONRenderer
from rest_framework.serializers import ModelSerializer
from rest_framework.viewsets import ModelViewSet, ReadOnlyModelViewSet

from .permissions import CombatantInfoPermission

logger = logging.getLogger("cards")


class CombatantListSerializer(ModelSerializer):
    class Meta:
        model = Combatant
        fields = [
            "legal_name",
            "sca_name",
            "card_id",
            "uuid",
            "accepted_privacy_policy",
        ]


class CombatantListViewSet(ReadOnlyModelViewSet):
    """
    API endpoint for the combatant list view
    """

    queryset = Combatant.objects.all()
    serializer_class = CombatantListSerializer
    renderer_classes = [JSONRenderer]
    permission_classes = [CombatantInfoPermission]


class CombatantSerializer(ModelSerializer):
    class Meta:
        model = Combatant
        fields = [
            "uuid",
            "email",
            "sca_name",
            "legal_name",
            "phone",
            "address1",
            "address2",
            "city",
            "province",
            "postal_code",
            "dob",
            "member_expiry",
            "member_number",
        ]

        extra_kwargs = {
            "dob": {"format": "%Y-%m-%d", "allow_null": True},
            "member_expiry": {"format": "%Y-%m-%d", "allow_null": True},
        }

    def validate(self, data):
        """
        Validate that member_expiry requires member_number and province code exists.
        """
        if data.get("member_expiry") and not data.get("member_number"):
            raise serializers.ValidationError(
                "If member_expiry is specified, member_number must also be specified."
            )

        # Validate province code exists in Region table
        if data.get("province"):
            province_code = data["province"]
            if not Region.objects.filter(code=province_code, active=True).exists():
                raise serializers.ValidationError(
                    f"Province code '{province_code}' is not valid. "
                    f"Valid codes are: {', '.join(Region.objects.filter(active=True).values_list('code', flat=True))}"
                )

        return data

    def to_internal_value(self, data):
        """
        Clean up blank strings for specified fields before validation
        """
        for attr in [
            "sca_name",
            "member_expiry",
            "member_number",
            "address2",
            "dob",
        ]:
            if attr in data and not data[attr]:
                data[attr] = None
        return super().to_internal_value(data)


class CombatantViewSet(ModelViewSet):
    """
    API endpoint that allows combatants to be viewed or edited.
    """

    queryset = Combatant.objects.all()
    serializer_class = CombatantSerializer
    renderer_classes = [JSONRenderer]
    permission_classes = [CombatantInfoPermission]
    lookup_field = "uuid"
