"""API endpoint for PIN reset initiation."""

import logging

from cards.mail import send_pin_reset
from cards.models.combatant import Combatant
from django.shortcuts import get_object_or_404
from feature_switches.helpers import is_enabled
from rest_framework import serializers, status
from rest_framework.response import Response
from rest_framework.views import APIView

from .permissions import InitiatePinResetPermission

logger = logging.getLogger("cards")


class InitiatePinResetSerializer(serializers.Serializer):
    """Serializer for PIN reset initiation requests."""

    combatant_uuid = serializers.UUIDField()


class InitiatePinResetView(APIView):
    """API endpoint for initiating a PIN reset for a combatant."""

    permission_classes = [InitiatePinResetPermission]

    def post(self, request):
        """Initiate a PIN reset for a combatant.

        Args:
            request: The HTTP request containing combatant_uuid in POST data.

        Returns:
            Response with success message or error details.
        """
        if not is_enabled("pin_authentication"):
            return Response(
                {"message": "PIN authentication is not enabled"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = InitiatePinResetSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        combatant = get_object_or_404(
            Combatant, uuid=serializer.validated_data["combatant_uuid"]
        )

        if not combatant.has_pin:
            return Response(
                {"message": f"{combatant.name} does not have a PIN set"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        reset_code = combatant.initiate_pin_reset()
        send_pin_reset(combatant, reset_code)

        logger.info(
            "PIN reset initiated for %s by %s", combatant.name, request.user.email
        )

        return Response(
            {"message": f"PIN reset email sent to {combatant.name}"},
            status=status.HTTP_200_OK,
        )
