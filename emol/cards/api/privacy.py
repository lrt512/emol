import logging

from cards.api.permissions import ResendPrivacyPermission
from cards.mail import send_privacy_policy
from cards.models.combatant import Combatant
from django.shortcuts import get_object_or_404
from rest_framework import serializers, status
from rest_framework.response import Response
from rest_framework.views import APIView

logger = logging.getLogger("cards")


class ResendPrivacySerializer(serializers.Serializer):
    combatant_uuid = serializers.UUIDField()

    # We never try to save anything but in case we do someday, we have not
    # implemented these methods.
    def create(self, validated_data):
        raise NotImplementedError("This serializer is read-only")

    def update(self, instance, validated_data):
        raise NotImplementedError("This serializer is read-only")


class ResendPrivacyView(APIView):
    """
    API endpoint for resending the privacy policy email to a combatant.
    """

    permission_classes = [ResendPrivacyPermission]

    def post(self, request):
        """
        Resend the privacy policy email to a combatant.

        POST data:
            combatant_uuid - The UUID of the combatant to resend the email to.
        """
        serializer = ResendPrivacySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        combatant = get_object_or_404(
            Combatant, uuid=serializer.validated_data["combatant_uuid"]
        )

        if combatant.accepted_privacy_policy:
            logger.warning(
                "Combatant %s has already accepted the privacy policy", combatant
            )
            return Response(
                {"message": f"{combatant.name} has accepted the privacy policy"},
                status=status.HTTP_208_ALREADY_REPORTED,
            )

        send_privacy_policy(combatant)
        # logger.info("Sent privacy policy reminder to %s", combatant.name)
        return Response(
            {"message": f"Sent privacy policy reminder to {combatant.name}"},
            status=status.HTTP_200_OK,
        )
