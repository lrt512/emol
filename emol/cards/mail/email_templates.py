# -*- coding: utf-8 -*-
"""Email templates.

Each template has two string elements:
    - subject line for the email
    - body of the email

Each body may define a number of named format elements for string.format.
It is up to the caller to ensure that all named elements are provided; no error
checking is provided here.

"""

# Template for waiver expiry reminder email
WAIVER_REMINDER_SUBJECT = "Waiver expiry reminder"
WAIVER_REMINDER_EMAIL = """Greetings, {combatant_name}!

The waiver you have on file with the Minister of the Lists will expire in
{expiry_days} days, on {expiry_date}. If your waiver expires, you will not
be able to participate in SCA combat activities until you file a new one.

You can find the waiver here:
http://www.ealdormere.ca/uploads/2/4/1/5/24151324/adult_waiver.pdf

Please print and fill one out, and then return it to the Minister of the Lists.

You can send it by postal mail, or scan and email it. Contact information
for the Minister of the Lists can be found here:
http://www.ealdormere.ca/earl-marshal-deputies.html

Ealdormere eMoL
"""

WAIVER_EXPIRY_SUBJECT = "Waiver expiry notice"
WAIVER_EXPIRY_EMAIL = """Greetings, {combatant_name}!

The waiver you have on file with the Minister of the Lists has expired.
Until you file a new waiver with the Minister of the Lists, you will not
be able to participate in SCA combat activities.

You can find the waiver here:
http://www.ealdormere.ca/uploads/2/4/1/5/24151324/adult_waiver.pdf

Please print and fill one out, and then return it to the Minister of the Lists.

You can send it by postal mail, or scan and email it. Contact information
for the Minister of the Lists can be found here:
http://www.ealdormere.ca/earl-marshal-deputies.html

Ealdormere eMoL
"""

# Template for card expiry reminder email
CARD_REMINDER_SUBJECT = "Card expiry reminder"
CARD_REMINDER_EMAIL = """Greetings, {combatant_name}!

Your Ealdormere authorizations for {discipline} will expire in {expiry_days}
days, on {expiry_date}. To renew them, please see your local marshal to fill
out the paperwork, then send it to the Minister of the Lists

You can send it by postal mail, or scan and email it. Contact information
for the Minister of the Lists can be found here:
http://www.ealdormere.ca/earl-marshal-deputies.html

Ealdormere eMoL
"""

# Template for card expiry reminder email
CARD_EXPIRY_SUBJECT = "Card expiry notice"
CARD_EXPIRY_EMAIL = """Greetings, {combatant_name}!

Your Ealdormere authorizations for {discipline} have expired as of today.
To renew them, please see your local marshal or contact the Minister of
the Lists. Contact information for the Minister of the Lists can be found here:
http://www.ealdormere.ca/earl-marshal-deputies.html

Ealdormere eMoL
"""

# Template for authorizaton card URL email
CARD_URL_SUBJECT = "Your authorization card"
CARD_URL_EMAIL = """Greetings, {combatant_name}!

Here is where you can view your authorization card online:
{card_url}

This location does not change, so you can bookmark it.

Ealdormere eMoL
"""

# Template for combatant self-serve info update email
INFO_UPDATE_SUBJECT = "Information update request"
INFO_UPDATE_EMAIL = """Greetings, {combatant_name}!

We have received a request to update your information.
If you did not make the request, you can safely ignore this email.

To update your information, use this link:
{update_url}

This link will be usable for 24 hours from the time it was requested,
after which it will expire and a new one must be requested.

Ealdormere eMoL
"""

# Template for welcome/privacy policy email
PRIVACY_POLICY_SUBJECT = "Welcome to Ealdormere eMoL!"
PRIVACY_POLICY_EMAIL = """Greetings, {combatant_name}!

Congratulations on your authorization!

Now, let's get your authorization card in order...

Ealdormere has moved to a fully-online card management system, the
Electronic Minister of the Lists, or eMoL.

However, by Canadian law, before we finalize you in the eMoL database you must
be given the option to opt-out and the ability to view and accept our privacy
policy before you make that decision. At the end of this email, you'll find a
link that will take you to the eMoL privacy policy. Give it a read and then
accept or decline it.

It's completely up to you whether you accept or decline. If you don't want
your information stored online by us, that's fine, just decline the privacy
policy. This is what happens in either case:

If You Accept
=============
We'll finalize your entry in the eMoL database and note that you accepted the
privacy policy. You will be able to:
- View your authorization card online
- Manage your information online
- Manage any new authorizations you get online
- Receive email notification when your card is getting close to expiry
- Receive email notification when your waiver on file is getting close to expiry

If You Decline
==============
We'll delete all trace of you from the eMoL database
- The MoL will track your authorizations and information manually, offline
- You will be mailed an authorization card
- When your card expires, you will have to either find the MoL in person, or
  mail them your card to be re-stamped with a new expiry date
- The MoL will track any new authorizations you get manually
- You won't get any automatic reminders about card expiry
- The MoL will still email you manually about waiver expiry

This link will take you to the privacy policy page.

{privacy_policy_url}

Please read the policy
carefully. It explains what information we store, how we protect it, and how
we use it. As above, accept or decline it and we'll go from there!

The link will be usable for one week from the date of this email, after which
it will expire and a new one must be requested.

Ealdormere eMoL
"""

# PIN setup required email
PIN_SETUP_SUBJECT = "Set your eMoL PIN"
PIN_SETUP_EMAIL = """Greetings, {combatant_name}!

To improve security, eMoL now requires a PIN to access your authorization card
and update your information.

Please set your PIN using the following link:
{pin_setup_url}

Your PIN must be 4-6 numeric digits. Choose something you can remember, but
don't use obvious numbers like your birth year or 1234.

This link will expire in 24 hours. If it expires before you set your PIN,
please contact the Minister of the Lists to request a new link.

Ealdormere eMoL
"""

# PIN lockout notification email
PIN_LOCKOUT_SUBJECT = "Your eMoL account has been temporarily locked"
PIN_LOCKOUT_EMAIL = """Greetings, {combatant_name}!

Your eMoL account has been temporarily locked due to multiple incorrect PIN
attempts. This is a security measure to protect your information.

Your account will be automatically unlocked in 15 minutes.

If you did not make these attempts, please contact the Minister of the Lists
immediately, as someone may be trying to access your account.

If you have forgotten your PIN, please contact the Minister of the Lists to
request a PIN reset.

Ealdormere eMoL
"""

# PIN reset email
PIN_RESET_SUBJECT = "Reset your eMoL PIN"
PIN_RESET_EMAIL = """Greetings, {combatant_name}!

A PIN reset has been initiated for your eMoL account by the Minister of the
Lists.

Please set your new PIN using the following link:
{pin_reset_url}

Your PIN must be 4-6 numeric digits. Choose something you can remember, but
don't use obvious numbers like your birth year or 1234.

This link will expire in 24 hours. If it expires before you set your PIN,
please contact the Minister of the Lists to request a new link.

Until you set a new PIN, you will not be able to access your authorization card.

Ealdormere eMoL
"""

# PIN migration campaign - initial email
PIN_MIGRATION_INITIAL_SUBJECT = "Action Required: Set your eMoL PIN"
PIN_MIGRATION_INITIAL_EMAIL = """Greetings, {combatant_name}!

To improve security, eMoL now requires a PIN to access your authorization card
and update your information.

Please set your PIN using the following link:
{pin_setup_url}

Your PIN must be 4-6 numeric digits. Choose something you can remember, but
don't use obvious numbers like your birth year or 1234.

This link will expire in 24 hours. If it expires before you set your PIN,
you can request a new link from the eMoL website.

Ealdormere eMoL
"""

# PIN migration campaign - reminder email
PIN_MIGRATION_REMINDER_SUBJECT = "Reminder: Set your eMoL PIN"
PIN_MIGRATION_REMINDER_EMAIL = """Greetings, {combatant_name}!

This is a reminder that you still need to set your eMoL PIN.

To improve security, eMoL now requires a PIN to access your authorization card
and update your information. We sent you an email about this last week.

Please set your PIN using the following link:
{pin_setup_url}

Your PIN must be 4-6 numeric digits. Choose something you can remember, but
don't use obvious numbers like your birth year or 1234.

This link will expire in 24 hours. If it expires before you set your PIN,
you can request a new link from the eMoL website.

Ealdormere eMoL
"""

# PIN migration campaign - final warning email
PIN_MIGRATION_FINAL_SUBJECT = "Final Notice: Set your eMoL PIN"
PIN_MIGRATION_FINAL_EMAIL = """Greetings, {combatant_name}!

This is the final notice regarding your eMoL PIN.

You have not yet set your PIN, which is now required to access your
authorization card online. If you do not set a PIN, you will need to contact
the Minister of the Lists directly to access your card information.

Please set your PIN using the following link:
{pin_setup_url}

Your PIN must be 4-6 numeric digits.

If you have any questions or difficulties, please contact the Minister of the
Lists for assistance.

Ealdormere eMoL
"""

# Map a dictionary of the above emails for reference
EMAIL_TEMPLATES = {
    "card_reminder": {"subject": CARD_REMINDER_SUBJECT, "body": CARD_REMINDER_EMAIL},
    "waiver_reminder": {
        "subject": WAIVER_REMINDER_SUBJECT,
        "body": WAIVER_REMINDER_EMAIL,
    },
    "card_expiry": {"subject": CARD_EXPIRY_SUBJECT, "body": CARD_EXPIRY_EMAIL},
    "waiver_expiry": {"subject": WAIVER_EXPIRY_SUBJECT, "body": WAIVER_EXPIRY_EMAIL},
    "card_url": {"subject": CARD_URL_SUBJECT, "body": CARD_URL_EMAIL},
    "info_update": {"subject": INFO_UPDATE_SUBJECT, "body": INFO_UPDATE_EMAIL},
    "privacy_policy": {"subject": PRIVACY_POLICY_SUBJECT, "body": PRIVACY_POLICY_EMAIL},
    "pin_setup": {"subject": PIN_SETUP_SUBJECT, "body": PIN_SETUP_EMAIL},
    "pin_lockout": {"subject": PIN_LOCKOUT_SUBJECT, "body": PIN_LOCKOUT_EMAIL},
    "pin_reset": {"subject": PIN_RESET_SUBJECT, "body": PIN_RESET_EMAIL},
    "pin_migration_initial": {
        "subject": PIN_MIGRATION_INITIAL_SUBJECT,
        "body": PIN_MIGRATION_INITIAL_EMAIL,
    },
    "pin_migration_reminder": {
        "subject": PIN_MIGRATION_REMINDER_SUBJECT,
        "body": PIN_MIGRATION_REMINDER_EMAIL,
    },
    "pin_migration_final": {
        "subject": PIN_MIGRATION_FINAL_SUBJECT,
        "body": PIN_MIGRATION_FINAL_EMAIL,
    },
}
