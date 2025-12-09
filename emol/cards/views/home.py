# -*- coding: utf-8 -*-
import logging
from typing import Any, Dict

from cards.mail import send_card_url, send_info_update, send_privacy_policy
from cards.models import Combatant, CombatantWarrant, Discipline, OneTimeCode
from current_user import get_current_user
from django.core.exceptions import MultipleObjectsReturned
from django.shortcuts import render
from django.template.defaulttags import register
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.http import require_http_methods
from feature_switches.helpers import is_enabled

logger = logging.getLogger("cards")


@register.filter
def get_item(dictionary: Dict[Any, Any], key: Any) -> Any:
    """Template filter to get dictionary item by key."""
    return dictionary.get(key)


def index(request):
    context = {
        "current_user": get_current_user(),
    }
    return render(request, "home/index.html", context)


def _find_combatants_by_email_and_pin(email: str, pin: str) -> list:
    """Find combatants matching email and PIN.

    Args:
        email: Email address to search for
        pin: PIN to verify

    Returns:
        List of combatants that match both email and PIN
    """
    combatants = Combatant.objects.filter(email=email)
    matching = []
    for combatant in combatants:
        if combatant.has_pin and combatant.check_pin(pin):
            matching.append(combatant)
        elif not combatant.has_pin:
            matching.append(combatant)
    return matching


@csrf_protect
@require_http_methods(["GET", "POST"])
def request_card(request):
    """Handle GET and POST methods for card requests."""
    pin_enabled = is_enabled("pin_authentication")

    if request.method == "GET":
        return render(request, "home/request_card.html", {"pin_enabled": pin_enabled})

    context = {
        "message": "If a combatant exists for this email, instructions have been sent."
    }
    email = request.POST.get("request-card-email", None)
    pin = request.POST.get("request-card-pin", "") if pin_enabled else ""

    try:
        if pin_enabled and pin:
            combatants = _find_combatants_by_email_and_pin(email, pin)
            if not combatants:
                context = {
                    "message": "No matching combatant found. Please check your email and PIN.",
                    "pin_enabled": pin_enabled,
                }
                return render(request, "home/request_card.html", context)

            for combatant in combatants:
                if combatant.accepted_privacy_policy:
                    send_card_url(combatant)
                else:
                    logger.error(f"Card request for {combatant} (privacy not accepted)")
                    send_privacy_policy(combatant)
        else:
            try:
                combatant = Combatant.objects.get(email=email)
                if combatant.accepted_privacy_policy:
                    send_card_url(combatant)
                else:
                    logger.error(f"Card request for {combatant} (privacy not accepted)")
                    send_privacy_policy(combatant)
            except MultipleObjectsReturned:
                combatants = Combatant.objects.filter(email=email)
                for combatant in combatants:
                    if combatant.accepted_privacy_policy:
                        send_card_url(combatant)
                    else:
                        send_privacy_policy(combatant)
    except Combatant.DoesNotExist:
        logger.error(f"Card URL request: No combatant for {email}")

    return render(request, "message/message.html", context)


@csrf_protect
@require_http_methods(["GET", "POST"])
def update_info(request):
    """Handle GET and POST methods for info update requests."""
    pin_enabled = is_enabled("pin_authentication")

    if request.method == "GET":
        return render(request, "home/update_info.html", {"pin_enabled": pin_enabled})

    email = request.POST.get("update-info-email", None)
    pin = request.POST.get("update-info-pin", "") if pin_enabled else ""
    context = {
        "message": ("If a combatant with this email exists, an email has been sent")
    }

    try:
        if pin_enabled and pin:
            combatants = _find_combatants_by_email_and_pin(email, pin)
            if not combatants:
                context = {
                    "message": "No matching combatant found. Please check your email and PIN.",
                    "pin_enabled": pin_enabled,
                }
                return render(request, "home/update_info.html", context)

            for combatant in combatants:
                if combatant.accepted_privacy_policy:
                    code = OneTimeCode.create_for_info_update(combatant)
                    logger.info(f"Created update code for {combatant}")
                    send_info_update(combatant, code)
                else:
                    logger.error(f"Card request for {combatant} (privacy not accepted)")
                    send_privacy_policy(combatant)
        else:
            try:
                combatant = Combatant.objects.get(email=email)
                if combatant.accepted_privacy_policy:
                    code = OneTimeCode.create_for_info_update(combatant)
                    logger.info(f"Created update code for {combatant}")
                    send_info_update(combatant, code)
                else:
                    logger.error(f"Card request for {combatant} (privacy not accepted)")
                    send_privacy_policy(combatant)
            except MultipleObjectsReturned:
                combatants = Combatant.objects.filter(email=email)
                for combatant in combatants:
                    if combatant.accepted_privacy_policy:
                        code = OneTimeCode.create_for_info_update(combatant)
                        logger.info(f"Created update code for {combatant}")
                        send_info_update(combatant, code)
                    else:
                        send_privacy_policy(combatant)

    except Combatant.DoesNotExist:
        logger.warning("No combatant found with email %s", email)

    return render(request, "message/message.html", context)


def message(request):
    """Render the message view."""
    return render(request, "message/message_embed.html")


def marshal_list(request):
    """Display the list of marshals by discipline.

    Retrieves all disciplines and their active marshals, organized by discipline.
    """
    logger.info("Fetching marshal list")

    disciplines = Discipline.objects.all().order_by("name")
    logger.debug(f"Found {disciplines.count()} disciplines")

    warrants = CombatantWarrant.objects.select_related(
        "card__combatant", "marshal", "marshal__discipline"
    ).order_by("card__combatant__sca_name")

    logger.debug(f"Found {warrants.count()} total warrants")

    marshal_lists = {}
    for warrant in warrants:
        try:
            if warrant.marshal is None:
                logger.warning(f"Warrant {warrant.id} has no associated marshal")
                continue

            discipline_id = warrant.marshal.discipline_id
            if discipline_id not in marshal_lists:
                marshal_lists[discipline_id] = []
            marshal_lists[discipline_id].append(warrant)
        except AttributeError as e:
            logger.error(f"Missing attribute for warrant {warrant.id}: {str(e)}")
        except ValueError as e:
            logger.error(f"Invalid data for warrant {warrant.id}: {str(e)}")

    logger.debug(f"Organized warrants into {len(marshal_lists)} discipline groups")

    context = {
        "disciplines": disciplines,
        "marshal_lists": marshal_lists,
    }

    return render(
        request,
        "home/marshal_list.html",
        context,
    )
