import logging

from cards.utility.privacy import privacy_policy_url
from emailer import AWSEmailer

from .email_templates import EMAIL_TEMPLATES

logger = logging.getLogger("cards")


def send_card_reminder(reminder):
    """Send a card reminder notice to a combatant.

    Callers should validate that reminder.content_object is a Card before calling.

    Args:
        reminder: A Reminder object
    """
    try:
        card = reminder.content_object
        template = EMAIL_TEMPLATES.get("card_reminder")
        body = template.get("body").format(
            expiry_days=reminder.days_to_expiry,
            expiry_date=card.expiration_date_str,
            discipline=card.discipline.name,
        )
        return AWSEmailer.send_email(
            card.combatant.email, template.get("subject"), body
        )
    except AttributeError:
        logger.error("Reminder %s does not have a card", reminder)
        return False


def send_card_expiry(reminder):
    """Send a card expiration notification to a combatant

    Callers should validate that reminder.content_object is a Card before calling.

    Args:
        reminder: A Reminder object
    """
    try:
        card = reminder.content_object
        template = EMAIL_TEMPLATES.get("card_expiry")
        body = template.get("body").format(
            discipline=card.discipline.name,
        )
        return AWSEmailer.send_email(
            card.combatant.email, template.get("subject"), body
        )
    except AttributeError:
        logger.error("Reminder %s does not have a card", reminder)
        return False


def send_waiver_reminder(reminder):
    """Send a waiver reminder notice to a combatant.

    Callers should validate that reminder.content_object is a Waiver before calling.

    Args:
        reminder: A Reminder object

    """
    try:
        waiver = reminder.content_object
        template = EMAIL_TEMPLATES.get("waiver_reminder")
        body = template.get("body").format(
            expiry_days=reminder.days_to_expiry,
            expiry_date=waiver.expiration_date_str,
        )
        return AWSEmailer.send_email(
            waiver.combatant.email, template.get("subject"), body
        )
    except AttributeError:
        logger.error("Reminder %s does not have a waiver", reminder)
        return False


def send_waiver_expiry(reminder):
    """Send a waiver expiry notice to a combatant.

    Callers should validate that reminder.content_object is a Waiver before calling.

    Args:
        reminder: A Reminder object
    """
    try:
        waiver = reminder.content_object
        template = EMAIL_TEMPLATES.get("waiver_expiry")
        body = template.get("body").format(
            expiry_days=reminder.days_to_expiry,
            expiry_date=reminder.due_date,
        )
        return AWSEmailer.send_email(
            waiver.combatant.email, template.get("subject"), body
        )
    except AttributeError:
        logger.error("Reminder %s does not have a waiver", reminder)
        return False


def send_info_update(combatant, update_code):
    """Send a information update link to a combatant.

    Args:
        combatant: The combatant to send notice to
        update_request: The update request

    """
    template = EMAIL_TEMPLATES.get("info_update")
    body = template.get("body").format(update_url=update_code.url)
    return AWSEmailer.send_email(combatant.email, template.get("subject"), body)


def send_card_url(combatant):
    """Send a combatant their card URL.

    Args:
        combatant: The combatant to send notice to

    Raises:
        PrivacyAcceptance.NotAccepted if the combatant has not
            yet accepted the privacy policy

    """
    template = EMAIL_TEMPLATES.get("card_url")
    body = template.get("body").format(card_url=combatant.card_url)
    return AWSEmailer.send_email(combatant.email, template.get("subject"), body)


def send_privacy_policy(combatant):
    """Send the privacy policy email to a combatant.

    Use the given PrivacyAcceptance record to get the email address and
    dispatch the email.

    Args:
        privacy_acceptance: A PrivacyAcceptance object to work from

    """
    template = EMAIL_TEMPLATES.get("privacy_policy")
    body = template.get("body").format(privacy_policy_url=privacy_policy_url(combatant))
    return AWSEmailer.send_email(combatant.email, template.get("subject"), body)
