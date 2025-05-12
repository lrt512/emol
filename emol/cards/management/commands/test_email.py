# -*- coding: utf-8 -*-
import logging

from django.core.management.base import BaseCommand

from emailer import AWSEmailer

logger = logging.getLogger("cards")

class Command(BaseCommand):
    help = "Send a test email to the address specified on the command line"

    def add_arguments(self, parser):
        parser.add_argument('recipient', type=str, help='The email address to send the test email to')

    def handle(self, *args, **kwargs):
        recipient = kwargs['recipient']
        subject = 'Test Email from eMoL'
        body = 'This is a test email sent by eMoL using the AWSEmailer class.'

        success = AWSEmailer.send_email(recipient, subject, body)

        if success:
            self.stdout.write(self.style.SUCCESS(f'Successfully sent test email to {recipient}'))
        else:
            self.stdout.write(self.style.ERROR(f'Failed to send test email to {recipient}'))
