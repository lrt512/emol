import logging

from rest_framework import serializers, status, viewsets
from rest_framework.generics import get_object_or_404
from rest_framework.renderers import JSONRenderer
from rest_framework.response import Response
from rest_framework.serializers import ModelSerializer

from cards.models.combatant import Combatant
from cards.models.waiver import Waiver

from .permissions import WaiverDatePermission

logger = logging.getLogger("cards")


class WaiverSerializer(ModelSerializer):
    uuid = serializers.UUIDField(required=False)

    class Meta:
        model = Waiver
        fields = [
            "uuid",
            "date_signed",
            "expiration_date",
        ]


class WaiverViewSet(viewsets.ModelViewSet):
    queryset = Waiver.objects.all()
    serializer_class = WaiverSerializer
    permission_classes = [WaiverDatePermission]
    renderer_classes = [JSONRenderer]
    lookup_field = "uuid"

    def retrieve(self, request, uuid):
        waiver = get_object_or_404(Waiver, combatant__uuid=uuid)
        serializer = WaiverSerializer(waiver)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def update(self, request, uuid):
        serializer = self.get_serializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)

        combatant = get_object_or_404(Combatant, uuid=uuid)

        try:
            waiver = Waiver.objects.get(combatant=combatant)
            waiver.date_signed = serializer.validated_data.get("date_signed")
        except Waiver.DoesNotExist:
            waiver = Waiver(
                combatant=combatant,
                date_signed=serializer.validated_data.get("date_signed"),
            )
        finally:
            logger.debug("save waiver")
            waiver.save()

        response_data = {
            "date_signed": waiver.date_signed,
            "expiration_date": waiver.expiration_date.strftime("%Y-%m-%d"),
        }
        return Response(response_data, status=status.HTTP_200_OK)
