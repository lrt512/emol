"""PIN-related views for combatant authentication."""

import logging

from cards.mail import send_pin_reset, send_pin_setup
from cards.models import Combatant, OneTimeCode
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect, render
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.http import require_http_methods
from feature_switches.helpers import is_enabled

logger = logging.getLogger("cards")


@csrf_protect
@require_http_methods(["GET", "POST"])
def pin_setup(request: HttpRequest, code: str) -> HttpResponse:
    """Handle initial PIN setup after privacy policy acceptance.

    Args:
        request: The HTTP request
        code: The one-time code for PIN setup

    Returns:
        Rendered template or redirect
    """
    if not is_enabled("pin_authentication"):
        return render(
            request,
            "message/message.html",
            {"message": "PIN authentication is not currently enabled."},
        )

    try:
        one_time_code = OneTimeCode.objects.get(code=code)

        if not one_time_code.is_valid:
            return render(
                request,
                "message/message.html",
                {"message": "This PIN setup link has expired or already been used."},
            )

        combatant = one_time_code.combatant

        if request.method == "GET":
            return render(
                request,
                "pin/setup.html",
                {"code": code, "combatant_name": combatant.name},
            )

        pin = request.POST.get("pin", "")
        pin_confirm = request.POST.get("pin_confirm", "")

        if pin != pin_confirm:
            return render(
                request,
                "pin/setup.html",
                {
                    "code": code,
                    "combatant_name": combatant.name,
                    "error": "PINs do not match.",
                },
            )

        try:
            combatant.set_pin(pin)
            one_time_code.consume()
            logger.info(f"PIN set successfully for combatant {combatant.email}")
            return render(
                request,
                "message/message.html",
                {
                    "message": "Your PIN has been set successfully. "
                    "You can now access your authorization card."
                },
            )
        except ValueError as e:
            return render(
                request,
                "pin/setup.html",
                {
                    "code": code,
                    "combatant_name": combatant.name,
                    "error": str(e),
                },
            )

    except (OneTimeCode.DoesNotExist, ValueError, ValidationError):
        return render(
            request,
            "message/message.html",
            {"message": "This PIN setup link is invalid or has expired."},
        )
    except Exception:
        logger.exception("Unexpected error in pin_setup for code %s", code)
        return render(
            request,
            "message/message.html",
            {"message": "An unexpected error occurred. Please try again later."},
        )


@csrf_protect
@require_http_methods(["GET", "POST"])
def pin_reset(request: HttpRequest, code: str) -> HttpResponse:
    """Handle PIN reset initiated by MoL.

    Args:
        request: The HTTP request
        code: The one-time code for PIN reset

    Returns:
        Rendered template or redirect
    """
    if not is_enabled("pin_authentication"):
        return render(
            request,
            "message/message.html",
            {"message": "PIN authentication is not currently enabled."},
        )

    try:
        one_time_code = OneTimeCode.objects.get(code=code)

        if not one_time_code.is_valid:
            return render(
                request,
                "message/message.html",
                {"message": "This PIN reset link has expired or already been used."},
            )

        combatant = one_time_code.combatant

        if request.method == "GET":
            return render(
                request,
                "pin/reset.html",
                {"code": code, "combatant_name": combatant.name},
            )

        pin = request.POST.get("pin", "")
        pin_confirm = request.POST.get("pin_confirm", "")

        if pin != pin_confirm:
            return render(
                request,
                "pin/reset.html",
                {
                    "code": code,
                    "combatant_name": combatant.name,
                    "error": "PINs do not match.",
                },
            )

        try:
            combatant.set_pin(pin)
            one_time_code.consume()
            logger.info(f"PIN reset successfully for combatant {combatant.email}")
            return render(
                request,
                "message/message.html",
                {
                    "message": "Your PIN has been reset successfully. "
                    "You can now access your authorization card."
                },
            )
        except ValueError as e:
            return render(
                request,
                "pin/reset.html",
                {
                    "code": code,
                    "combatant_name": combatant.name,
                    "error": str(e),
                },
            )

    except (OneTimeCode.DoesNotExist, ValueError, ValidationError):
        return render(
            request,
            "message/message.html",
            {"message": "This PIN reset link is invalid or has expired."},
        )
    except Exception:
        logger.exception("Unexpected error in pin_reset for code %s", code)
        return render(
            request,
            "message/message.html",
            {"message": "An unexpected error occurred. Please try again later."},
        )


@csrf_protect
@require_http_methods(["GET", "POST"])
def pin_verify(request: HttpRequest, card_id: str) -> HttpResponse:
    """Verify PIN before showing card.

    Args:
        request: The HTTP request
        card_id: The combatant's card ID

    Returns:
        Redirect to card view or error message
    """
    if not is_enabled("pin_authentication"):
        return redirect("combatant-card", card_id=card_id)

    try:
        combatant = Combatant.objects.get(card_id=card_id)

        if not combatant.has_pin:
            return redirect("combatant-card", card_id=card_id)

        if combatant.is_locked_out:
            return render(
                request,
                "message/message.html",
                {
                    "message": "Your account is temporarily locked due to multiple "
                    "incorrect PIN attempts. Please try again later or contact "
                    "the Minister of the Lists."
                },
            )

        if request.method == "GET":
            return render(
                request,
                "pin/verify.html",
                {"card_id": card_id, "combatant_name": combatant.name},
            )

        pin = request.POST.get("pin", "")

        if combatant.check_pin(pin):
            request.session[f"pin_verified_{card_id}"] = True
            return redirect("combatant-card", card_id=card_id)

        remaining_attempts = combatant.PIN_MAX_ATTEMPTS - combatant.pin_failed_attempts
        error_msg = f"Incorrect PIN. {remaining_attempts} attempts remaining."

        if combatant.is_locked_out:
            return render(
                request,
                "message/message.html",
                {
                    "message": "Your account has been temporarily locked due to "
                    "multiple incorrect PIN attempts. You will receive an email "
                    "notification. Please try again in 15 minutes."
                },
            )

        return render(
            request,
            "pin/verify.html",
            {
                "card_id": card_id,
                "combatant_name": combatant.name,
                "error": error_msg,
            },
        )

    except Combatant.DoesNotExist:
        return render(
            request,
            "message/message.html",
            {"message": "Card not found."},
        )
    except Exception:
        logger.exception("Unexpected error in pin_verify for card_id %s", card_id)
        return render(
            request,
            "message/message.html",
            {"message": "An unexpected error occurred. Please try again later."},
        )


def initiate_pin_reset_for_combatant(combatant: Combatant) -> OneTimeCode:
    """Initiate a PIN reset for a combatant (called by MoL).

    Args:
        combatant: The combatant to reset PIN for

    Returns:
        OneTimeCode for the PIN reset
    """
    one_time_code = combatant.initiate_pin_reset()
    send_pin_reset(combatant, one_time_code)
    logger.info(f"PIN reset initiated for combatant {combatant.email}")
    return one_time_code


def send_pin_setup_email(combatant: Combatant) -> OneTimeCode:
    """Send PIN setup email to combatant.

    Args:
        combatant: The combatant to send setup email to

    Returns:
        OneTimeCode for the PIN setup
    """
    one_time_code = OneTimeCode.create_for_pin_setup(combatant)
    send_pin_setup(combatant, one_time_code)
    logger.info(f"PIN setup email sent to combatant {combatant.email}")
    return one_time_code
