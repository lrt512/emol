# -*- coding: utf-8 -*-
"""Model an authorization card.

    A card represents a single martial discipline.

    Card
    |
    - Discipline (via discipline_id)
    |
    - Authorizations (Authorization model via CombatantAuthorization)
    |
    - Warrants (Marshal model via Warrant)
    |
    - Card Date (The date auths were renewed, not the expiry date)

    A combatant may hold one card for each discipline they have authorizations
    in. These show up as the `cards` relationship on the Combatant model.
"""

from dateutil.relativedelta import relativedelta

from flask import current_app as app
from flask_login import current_user

from emol.mail import Emailer
from emol.mail.email_templates import EMAIL_TEMPLATES
from emol.utility.date import add_years, today, DATE_FORMAT, LOCAL_TZ

from .authorization import Authorization
from .config import Config
from .marshal import Marshal

__all__ = ['Card']


class Card(app.db.Model):
    """Model an authorization card

    Card date is the date that the card was renewed.
    The card_expiry property gives the expiry date

    Discipline will be none if card date is global

    Attributes:
        id: Primary key in the database
        combatant_id: The combatant's id
        discipline_id: ID of the discipline this card is for
        card_date: Date this card was last renewed
        authorizations: Authorizations attached to this card
            (Authorization model via CombatantAuthorization)
        warrants: Marshal warrants attached to this card
            (Marshal model via Warrant)

    Properties:
        expiry_date: The card's expiry date
        expiry_date_str: Expiry date as formatted string
        expiry_days: Number of days until expiry

    Backrefs:
        reminders: This card's expiry reminders
    """

    __table_args__ = (
        app.db.UniqueConstraint('combatant_id', 'discipline_id'),
    )

    id = app.db.Column(
        app.db.Integer,
        primary_key=True
    )

    combatant_id = app.db.Column(
        app.db.Integer,
        app.db.ForeignKey('combatant.id')
    )
    combatant = app.db.relationship('Combatant', uselist=False)

    discipline_id = app.db.Column(
        app.db.Integer,
        app.db.ForeignKey('discipline.id')
    )
    discipline = app.db.relationship('Discipline')

    authorizations = app.db.relationship(
        'Authorization',
        secondary='combatant_authorization'
    )

    warrants = app.db.relationship(
        'Marshal',
        secondary='warrant'
    )

    card_date = app.db.Column(app.db.Date)

    @classmethod
    def create(cls, combatant, discipline):
        """Create a card.

        Args:
            combatant: A Combatant object
            discipline: A Discipline object

        Returns:
            A Card object

        """
        if current_user.has_role(discipline, 'edit_authorizations') is False:
            raise Exception('no')

        card = cls(combatant_id=combatant.id, discipline_id=discipline.id)
        app.db.session.add(card)
        app.db.session.commit()
        app.db.session.refresh(card)

        card.renew()
        return card

    @property
    def expiry_date(self):
        """Get the combatant's authorization card expiry date.

        That is, the self.card + CARD_DURATION years

        Returns:
            Date of the card's expiry date as a string

        """
        return add_years(self.card_date, 2)

    @property
    def expiry_date_str(self):
        """Get the combatant's authorization card expiry date as a string."""
        return self.expiry_date.strftime(DATE_FORMAT)

    @property
    def expiry_days(self):
        """Number of days until this card expires."""
        return (self.expiry_date - today()).days

    def add_authorization(self, authorization):
        """Add an authorization to this card.

        Args:
            authorization: An authorization slug, id, or object

        """
        if current_user.has_role(self.discipline, 'edit_authorizations') is False:
            raise Exception('no')

        authorization = Authorization.find(self.discipline, authorization)

        if authorization in self.authorizations:
            return

        self.authorizations.append(authorization)
        app.db.session.commit()

    def remove_authorization(self, authorization):
        """Remove an authorization to this card.

        Args:
            authorization: An authorization slug, id, or object

        """
        if current_user.has_role(self.discipline, 'edit_authorizations') is False:
            raise Exception('no')

        authorization = Authorization.find(self.discipline, authorization)

        if authorization not in self.authorizations:
            return

        self.authorizations.remove(authorization)
        app.db.session.commit()

    def has_authorization(self, authorization):
        """Check if the given authorization is on the card

        Args:
            authorization: An authorization slug, id, or object

        """
        authorization = Authorization.find(self.discipline, authorization)

        return authorization in self.authorizations

    def add_warrant(self, marshal):
        """Add an authorization to this card.

        Args:
            marshal: A marshal slug, id, or object

        """
        if current_user.has_role(self.discipline, 'edit_marshal') is False:
            raise Exception('no')

        marshal = Marshal.find(self.discipline, marshal)

        if marshal in self.warrants:
            return

        self.warrants.append(marshal)
        app.db.session.commit()

    def remove_warrant(self, marshal):
        """Remove a warrant for this discipline.

        Args:
            marshal: A marshal slug, id, or object

        """
        if current_user.has_role(self.discipline, 'edit_marshal') is False:
            raise Exception('no')

        marshal = Marshal.find(self.discipline, marshal)

        if marshal not in self.warrants:
            return

        self.warrants.remove(marshal)
        app.db.session.commit()

    def has_warrant(self, marshal):
        """Check if the given warrant is on the card

        Args:
            marshal: A marshal slug, id, or object

        """
        marshal = Marshal.find(self.discipline, marshal)

        return marshal in self.warrants

    def renew(self, card_date=None):
        """Renew this card.

        Args:
            card_date: Optional card date, defaults to today.

        """
        # Delete any existing reminders
        self.reminders.clear()

        # Update the card date
        self.card_date = card_date or today()

        # Create the reminder for expiry day
        expiry_date = (self.card_date + relativedelta(years=2))

        days_to_expiry = (expiry_date - today()).days
        # If already expired, don't need reminders
        if days_to_expiry <= 0:
            return

        # Expiry notice
        CardReminder.schedule(self, expiry_date, is_expiry=True)

        reminders = Config.get('card_reminders')
        reminders.sort()
        reminders_scheduled = 0

        # Reminders at the specified points before expiry day
        for days in reminders:
            # Don't send reminders for the past
            if days_to_expiry - days < 0:
                continue

            # Schedule for future date
            reminder_date = expiry_date - relativedelta(days=days)
            CardReminder.schedule(self, reminder_date, is_expiry=False)
            reminders_scheduled += 1

        # No reminders? Make sure there's one tonight then because all reminder
        # days are in the past.
        if reminders_scheduled == 0:
            CardReminder.schedule(self, today(), is_expiry=False)

        app.db.session.commit()


class CardReminder(app.db.Model):
    """Card expiry reminder.

    These will be scheduled by Card when the card date(s) are set or changed.

    """

    id = app.db.Column(app.db.Integer, primary_key=True)
    reminder_date = app.db.Column(app.db.Date)

    card_id = app.db.Column(app.db.Integer, app.db.ForeignKey('card.id'))
    card = app.db.relationship(
        'Card',
        backref=app.db.backref('reminders', cascade='all, delete-orphan')
    )
    is_expiry = app.db.Column(app.db.Boolean, nullable=False)

    def mail(self):
        """Send reminder or expiry email as appropriate to this instance."""

        discipline = self.card.discipline
        if self.is_expiry is True:
            template = EMAIL_TEMPLATES.get('card_expiry')
            subject = template.get('subject')
            body = template.get('body').format(
                discipline=discipline.name
            )
        else:
            template = EMAIL_TEMPLATES.get('card_reminder')
            subject = template.get('subject')
            body = template.get('body').format(
                expiry_days=self.card.expiry_days,
                expiry_date=self.card.expiry_date_str,
                discipline=discipline.name
            )

        return Emailer().send_email(self.card.combatant.email, subject, body)


    @classmethod
    def schedule(cls, card, reminder_date, is_expiry):
        """Schedule a card reminder.

        Args:
            card: The card to schedule for
            reminder_date: The date of the reminder
            is_expiry: True if the scheduled reminder is for expiry

        """
        app.logger.debug(
            'schedule card {0} ({1}) for {2}'.format(
                'expiry' if is_expiry else 'reminder',
                card.discipline.slug,
                reminder_date
            )
        )
        reminder = CardReminder(
            reminder_date=reminder_date,
            card_id=card.id,
            is_expiry=is_expiry
        )
        app.db.session.add(reminder)

    app.db.session.commit()
