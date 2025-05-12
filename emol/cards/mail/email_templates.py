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
WAIVER_REMINDER_EMAIL = """Greetings!

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
WAIVER_EXPIRY_EMAIL = """Greetings!

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
CARD_REMINDER_EMAIL = """Greetings!

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
CARD_EXPIRY_EMAIL = """Greetings!

Your Ealdormere authorizations for {discipline} have expired as of today.
To renew them, please see your local marshal or contact the Minister of
the Lists. Contact information for the Minister of the Lists can be found here:
http://www.ealdormere.ca/earl-marshal-deputies.html

Ealdormere eMoL
"""

# Template for authorizaton card URL email
CARD_URL_SUBJECT = "Your authorization card"
CARD_URL_EMAIL = """Greetings!

Here is where you can view your authorization card online:
{card_url}

This location does not change, so you can bookmark it.

Ealdormere eMoL
"""

# Template for combatant self-serve info update email
INFO_UPDATE_SUBJECT = "Information update request"
INFO_UPDATE_EMAIL = """Greetings!

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
PRIVACY_POLICY_EMAIL = """Greetings!

Congratulations on your authorization!

Now, let's get your authorization card in order...

In late 2022, Ealdormere moved to a fully-online card management system, the
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
}
