import logging

from cards.models.combatant import Combatant
from cards.models.privacy_policy import PrivacyPolicy
from django.http import HttpResponseBadRequest
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_http_methods
from feature_switches.helpers import is_enabled

logger = logging.getLogger("cards")


@require_http_methods(["GET", "POST"])
def privacy_policy(request, code=None):
    """View the privacy policy, optionally with UUID for accepting it.

    Args:
        code: Code for a Combatant's privacy_acceptance_code field
    """
    combatant = None
    code = request.POST.get("code", code)
    if code is not None:
        combatant = get_object_or_404(Combatant, privacy_acceptance_code=code)

    context = {"policy": PrivacyPolicy.latest_text()}
    if request.method == "POST":
        if combatant is None:
            raise HttpResponseBadRequest

        if "accept" in request.POST:
            combatant.accept_privacy_policy()

            if is_enabled("pin_authentication"):
                pin_code = combatant.one_time_codes.create_pin_setup_code()
                return redirect("pin-setup", code=pin_code.code)
            else:
                context = {
                    "card_url": combatant.card_url,
                    "sent_email": True,
                }
                return render(request, "privacy/privacy_accepted.html", context)
        elif "decline" in request.POST:
            combatant.delete()
            return render(request, "privacy/privacy_declined.html", {})
    elif request.method == "GET":
        context["code"] = code if combatant is not None else None
        if combatant is not None:
            logger.debug(f"privacy acceptance for combatant {combatant}")

        return render(request, "privacy/privacy_policy.html", context)
