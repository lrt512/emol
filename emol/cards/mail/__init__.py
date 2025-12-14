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
            combatant_name=card.combatant.name,
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
            combatant_name=card.combatant.name,
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
            combatant_name=waiver.combatant.name,
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
            combatant_name=waiver.combatant.name,
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
    body = template.get("body").format(
        update_url=update_code.url, combatant_name=combatant.name
    )
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
    body = template.get("body").format(
        card_url=combatant.card_url, combatant_name=combatant.name
    )
    return AWSEmailer.send_email(combatant.email, template.get("subject"), body)


def send_privacy_policy(combatant):
    """Send the privacy policy email to a combatant.

    Use the given PrivacyAcceptance record to get the email address and
    dispatch the email.

    Args:
        privacy_acceptance: A PrivacyAcceptance object to work from

    """
    template = EMAIL_TEMPLATES.get("privacy_policy")
    body = template.get("body").format(
        privacy_policy_url=privacy_policy_url(combatant), combatant_name=combatant.name
    )
    return AWSEmailer.send_email(combatant.email, template.get("subject"), body)


def send_pin_setup(combatant, one_time_code):
    """Send a PIN setup email to a combatant.

    Args:
        combatant: The combatant to send notice to
        one_time_code: The OneTimeCode for PIN setup

    Raises:
        ValueError: If combatant has not accepted the privacy policy
    """
    if not combatant.accepted_privacy_policy:
        raise ValueError(
            f"Cannot send PIN setup email to {combatant.email}: "
            "privacy policy not accepted"
        )

    template = EMAIL_TEMPLATES.get("pin_setup")
    body = template.get("body").format(
        pin_setup_url=one_time_code.url,
        combatant_name=combatant.name,
    )
    return AWSEmailer.send_email(combatant.email, template.get("subject"), body)


def send_pin_lockout_notification(combatant):
    """Send a PIN lockout notification to a combatant.

    Args:
        combatant: The combatant who has been locked out
    """
    template = EMAIL_TEMPLATES.get("pin_lockout")
    body = template.get("body").format(combatant_name=combatant.name)
    return AWSEmailer.send_email(combatant.email, template.get("subject"), body)


def send_pin_reset(combatant, one_time_code):
    """Send a PIN reset email to a combatant.

    Args:
        combatant: The combatant to send notice to
        one_time_code: The OneTimeCode for PIN reset
    """
    template = EMAIL_TEMPLATES.get("pin_reset")
    body = template.get("body").format(
        pin_reset_url=one_time_code.url,
        combatant_name=combatant.name,
    )
    return AWSEmailer.send_email(combatant.email, template.get("subject"), body)


def send_pin_migration_email(combatant, one_time_code, stage="initial"):
    """Send a PIN migration campaign email to a combatant.

    Args:
        combatant: The combatant to send notice to
        one_time_code: The OneTimeCode for PIN setup
        stage: One of 'initial', 'reminder', or 'final'

    Raises:
        ValueError: If combatant has not accepted the privacy policy
    """
    if not combatant.accepted_privacy_policy:
        raise ValueError(
            f"Cannot send PIN migration email to {combatant.email}: "
            "privacy policy not accepted"
        )

    template_key = f"pin_migration_{stage}"
    template = EMAIL_TEMPLATES.get(template_key)
    if not template:
        logger.error(f"Unknown PIN migration stage: {stage}")
        return False

    body = template.get("body").format(
        pin_setup_url=one_time_code.url,
        combatant_name=combatant.name,
    )
    return AWSEmailer.send_email(combatant.email, template.get("subject"), body)
