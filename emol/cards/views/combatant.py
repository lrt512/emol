# -*- coding: utf-8 -*-
"""Handlers for combatant administration views."""
import logging

from cards.models import Authorization, Combatant, Discipline, Region
from cards.utility.decorators import permission_required
from current_user import get_current_user
from django.shortcuts import redirect, render
from feature_switches.helpers import is_enabled

logger = logging.getLogger("cards")


@permission_required("read_combatant_info")
def combatant_list(request):
    """Handle requests to view the user list.

    DataTables will use the combatant API to get combatant data via AJAX

    """
    return render(request, "combatant/combatant_list.html")


@permission_required("read_combatant_info")
def combatant_detail(request):
    """Render the combatant detail form skeleton.

    A subsequent GET to /api/combatant/<uuid> should follow to populate
    the form fields if editing an existing combatant.
    """
    context = {
        "user": get_current_user(),
        "disciplines": Discipline.objects.all(),
        "authorizations": Authorization.objects.all(),
        "regions": Region.objects.all(),
        "combatant": {},
        "uuid": "",
    }
    return render(request, "combatant/combatant_detail.html", context)


def combatant_card(request, card_id):
    """View a combatant's card, accessed by its card_id.

    Args:
        card_id: The ID of the card to view
    """
    try:
        combatant = Combatant.objects.get(card_id=card_id)

        if is_enabled("pin_authentication") and combatant.has_pin:
            session_key = f"pin_verified_{card_id}"
            if not request.session.get(session_key):
                return redirect("pin-verify", card_id=card_id)

        if not hasattr(combatant, "waiver"):
            return render(request, "combatant/waiver_expired.html", {})

        context = {
            "legal_name": combatant.legal_name,
            "sca_name": combatant.sca_name,
            "waiver_expiry": combatant.waiver.expiry_or_expired,
            "cards": combatant.cards,
        }
        return render(request, "combatant/card.html", context)
    except Combatant.DoesNotExist:
        return redirect("/")
