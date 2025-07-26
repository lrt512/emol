# -*- coding: utf-8 -*-
import logging
from typing import Any, Dict

from cards.mail import send_card_url, send_info_update, send_privacy_policy
from cards.models import Combatant, CombatantWarrant, Discipline, UpdateCode

from current_user import get_current_user
from django.views.decorators.csrf import csrf_protect
from django.shortcuts import render
from django.template.defaulttags import register
from django.views.decorators.http import require_http_methods

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



@csrf_protect
@require_http_methods(["GET", "POST"])
def request_card(request):
    """Handle GET and POST methods for card requests."""
    if request.method == "GET":
        return render(request, "home/request_card.html")
    elif request.method == "POST":
        context = {
            "message": "If a combatant exists for this email, instructions have been sent."
        }
        email = request.POST.get("request-card-email", None)

        try:
            combatant = Combatant.objects.get(email=email)
            if combatant.accepted_privacy_policy:
                send_card_url(combatant)
            else:
                logger.error(f"Card request for {combatant} (privacy not accepted)")
                send_privacy_policy(combatant.privacy_acceptance)
        except Combatant.DoesNotExist:
            logger.error(f"Card URL request: No combatant for {email}")

        return render(request, "message/message.html", context)


@csrf_protect
@require_http_methods(["GET", "POST"])
def update_info(request):
    """Handle GET and POST methods for info update requests."""
    if request.method == "GET":
        return render(request, "home/update_info.html")
    elif request.method == "POST":
        email = request.POST.get("update-info-email", None)
        try:
            context = {}
            combatant = Combatant.objects.get(email=email)
            if combatant.accepted_privacy_policy:
                code, created = UpdateCode.objects.get_or_create(combatant=combatant)
                if created:
                    logger.info(f"Created update code for {combatant}")
                    code.save()
                send_info_update(combatant, code)
            else:
                logger.error(f"Card request for {combatant} (privacy not accepted)")
                send_privacy_policy(combatant.privacy_acceptance)

            context["message"] = (
                "If a combatant with this email exists, "
                "an email has been sent with instructions for "
                "updating your information"
            )
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

    # Get all warrants with related combatant and marshal info
    warrants = CombatantWarrant.objects.select_related(
        "card__combatant", "marshal", "marshal__discipline"
    ).order_by("card__combatant__sca_name")

    logger.debug(f"Found {warrants.count()} total warrants")

    # Organize warrants by discipline
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
