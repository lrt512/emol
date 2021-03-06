# -*- coding: utf-8 -*-
"""Daily check for card and waiver expiry reminders.

The daily check is invoked via the cron API, well, once per day.

"""

# standard library imports
from datetime import datetime

# third-party imports
from flask import current_app

# application imports
from emol.models import CardReminder, WaiverReminder
from emol.utility.date import today


def daily_check():
    """Perform the daily check for card and waiver reminders.

    Check CardReminder and WaiverReminder for any records with a
    date of today or earlier (any earlier records most likely did not get
    processed for whatever reason on their date). Fire off the reminder email
    for each found record, then delete the record.

    """
    current_app.logger.info('Daily check initiated')

    this_day = today()
    reminders = CardReminder.query.filter(CardReminder.reminder_date <= this_day).all()
    for reminder in reminders:
        current_app.logger.debug('Mail {0}'.format(reminder))
        reminder.mail()
        current_app.db.session.delete(reminder)

    reminders = WaiverReminder.query.filter(WaiverReminder.reminder_date <= this_day).all()
    for reminder in reminders:
        current_app.logger.debug('Mail {0}'.format(reminder))
        reminder.mail()
        current_app.db.session.delete(reminder)

    current_app.db.session.commit()

    current_app.logger.info('Daily check complete')
