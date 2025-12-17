# -*- coding: utf-8 -*-

import logging

from botocore.exceptions import ClientError
from django.conf import settings

from emol.secrets import get_aws_session

logger = logging.getLogger("cards")


class AWSEmailer:
    """A simple emailing facility that uses AWS SES

    SES configuration in settings.py:
        AWS_REGION = your AWS region
        MAIL_DEFAULT_SENDER = 'ealdormere.emol@gmail.com'
        MOL_EMAIL = 'ealdormere.mol@gmail.com'

    """

    CHARSET = "UTF-8"

    @classmethod
    def send_email(cls, recipient, subject, body, from_email=None, reply_to=None):
        """Send an email

        Args:
            recipient: Recipient's email address
            subject: The email's subject
            body: Email message text
            from_email: Optional sender email address
            reply_to: Optional reply-to email address (defaults to settings.MOL_EMAIL)

        Returns:
            True if the message was delivered

        """
        if settings.SEND_EMAIL is False:
            logger.info("Not sending email to %s", recipient)
            logger.info(subject)
            logger.info(body)
            return True
        else:
            logger.info("Sending email to %s: %s", recipient, subject)

        from_email = from_email or settings.MAIL_DEFAULT_SENDER
        reply_to = reply_to or settings.MOL_EMAIL
        sender = f"Ealdormere eMoL <{from_email}>"

        session = get_aws_session()
        client = session.client("ses")
        try:
            email_args = {
                "Destination": {
                    "ToAddresses": [
                        recipient,
                    ],
                },
                "Message": {
                    "Body": {
                        "Text": {"Charset": cls.CHARSET, "Data": body},
                    },
                    "Subject": {
                        "Charset": cls.CHARSET,
                        "Data": subject,
                    },
                },
                "Source": sender,
                "ReplyToAddresses": [reply_to],  # Always include reply-to
            }

            response = client.send_email(**email_args)

        except ClientError as exc:
            logger.error(f"Error sending mail to {recipient}")
            logger.exception(exc)
            return False
        else:
            logger.debug(
                "Email %s sent to %s. Message ID: %s",
                subject,
                recipient,
                response["MessageId"],
            )
            return True
