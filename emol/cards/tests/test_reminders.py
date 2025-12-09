"""Tests for reminder functionality."""

from datetime import timedelta
from unittest.mock import MagicMock, patch

from cards.models import (Authorization, Card, Combatant, Discipline, Reminder,
                          Waiver)
from cards.utility.time import today
from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.core.management import call_command
from django.test import TestCase, override_settings


class ReminderModelTestCase(TestCase):
    """Tests for the Reminder model."""

    def setUp(self):
        """Set up test fixtures."""
        self.discipline = Discipline.objects.create(
            name="Test Combat", slug="test-combat"
        )
        self.authorization = Authorization.objects.create(
            name="Test Auth", slug="test-auth", discipline=self.discipline
        )
        self.combatant = Combatant.objects.create(
            sca_name="Test Fighter",
            legal_name="Test Legal",
            email="test@example.com",
            accepted_privacy_policy=True,
        )

    @override_settings(REMINDER_DAYS=[60, 30, 14, 0])
    def test_create_or_update_reminders_creates_all_reminder_days(self):
        """Reminders are created for each day in REMINDER_DAYS."""
        card = Card.objects.create(
            combatant=self.combatant,
            discipline=self.discipline,
            date_issued=today(),
        )

        reminders = Reminder.objects.filter(
            content_type=ContentType.objects.get_for_model(Card),
            object_id=card.id,
        )

        self.assertEqual(reminders.count(), 4)
        days = set(reminders.values_list("days_to_expiry", flat=True))
        self.assertEqual(days, {60, 30, 14, 0})

    @override_settings(REMINDER_DAYS=[60, 30, 14, 0])
    def test_create_or_update_reminders_calculates_due_dates(self):
        """Due dates are calculated from expiration date."""
        card = Card.objects.create(
            combatant=self.combatant,
            discipline=self.discipline,
            date_issued=today(),
        )
        expiration = card.expiration_date

        for reminder in Reminder.objects.filter(object_id=card.id):
            expected_due = expiration - timedelta(days=reminder.days_to_expiry)
            self.assertEqual(reminder.due_date, expected_due)

    @override_settings(REMINDER_DAYS=[60, 30, 14, 0])
    def test_create_or_update_reminders_replaces_existing(self):
        """Updating reminders deletes old ones and creates new."""
        card = Card.objects.create(
            combatant=self.combatant,
            discipline=self.discipline,
            date_issued=today() - timedelta(days=365),
        )
        old_reminder_ids = list(
            Reminder.objects.filter(object_id=card.id).values_list("id", flat=True)
        )

        card.date_issued = today()
        card.save()

        new_reminders = Reminder.objects.filter(object_id=card.id)
        self.assertEqual(new_reminders.count(), 4)
        for old_id in old_reminder_ids:
            self.assertFalse(Reminder.objects.filter(id=old_id).exists())

    def test_should_send_email_returns_false_without_privacy_acceptance(self):
        """should_send_email returns False if combatant hasn't accepted privacy."""
        combatant_no_privacy = Combatant.objects.create(
            sca_name="No Privacy",
            legal_name="No Privacy Legal",
            email="noprivacy@example.com",
            accepted_privacy_policy=False,
        )
        card = Card.objects.create(
            combatant=combatant_no_privacy,
            discipline=self.discipline,
            date_issued=today(),
        )
        reminder = Reminder.objects.filter(object_id=card.id).first()

        self.assertFalse(reminder.should_send_email)

    def test_should_send_email_returns_true_with_privacy_acceptance(self):
        """should_send_email returns True if combatant accepted privacy."""
        card = Card.objects.create(
            combatant=self.combatant,
            discipline=self.discipline,
            date_issued=today(),
        )
        reminder = Reminder.objects.filter(object_id=card.id).first()

        self.assertTrue(reminder.should_send_email)

    def test_should_send_email_returns_false_for_orphaned_reminder(self):
        """should_send_email returns False if content_object is None."""
        card_ct = ContentType.objects.get_for_model(Card)
        orphaned = Reminder.objects.create(
            content_type=card_ct,
            object_id=99999,
            days_to_expiry=30,
            due_date=today(),
        )

        self.assertFalse(orphaned.should_send_email)

    @patch("cards.models.card.send_card_reminder")
    def test_send_email_returns_true_on_success(self, mock_send):
        """send_email returns True when email is sent successfully."""
        mock_send.return_value = True
        card = Card.objects.create(
            combatant=self.combatant,
            discipline=self.discipline,
            date_issued=today(),
        )
        reminder = Reminder.objects.filter(object_id=card.id, days_to_expiry=30).first()

        result = reminder.send_email()

        self.assertTrue(result)
        mock_send.assert_called_once()

    @patch("cards.models.card.send_card_reminder")
    def test_send_email_returns_false_on_failure(self, mock_send):
        """send_email returns False when email fails."""
        mock_send.return_value = False
        card = Card.objects.create(
            combatant=self.combatant,
            discipline=self.discipline,
            date_issued=today(),
        )
        reminder = Reminder.objects.filter(object_id=card.id, days_to_expiry=30).first()

        result = reminder.send_email()

        self.assertFalse(result)

    @patch("cards.models.card.send_card_expiry")
    def test_send_email_calls_expiry_for_zero_days(self, mock_send):
        """send_email calls send_expiry for 0-day reminders."""
        mock_send.return_value = True
        card = Card.objects.create(
            combatant=self.combatant,
            discipline=self.discipline,
            date_issued=today(),
        )
        reminder = Reminder.objects.filter(object_id=card.id, days_to_expiry=0).first()

        reminder.send_email()

        mock_send.assert_called_once()

    def test_send_email_returns_false_without_privacy(self):
        """send_email returns False without calling mailer if no privacy acceptance."""
        combatant_no_privacy = Combatant.objects.create(
            sca_name="No Privacy",
            legal_name="No Privacy Legal",
            email="noprivacy@example.com",
            accepted_privacy_policy=False,
        )
        card = Card.objects.create(
            combatant=combatant_no_privacy,
            discipline=self.discipline,
            date_issued=today(),
        )
        reminder = Reminder.objects.filter(object_id=card.id).first()

        with patch("cards.models.card.send_card_reminder") as mock_send:
            result = reminder.send_email()

        self.assertFalse(result)
        mock_send.assert_not_called()


class CardReminderSignalTestCase(TestCase):
    """Tests for Card post_save signal creating reminders."""

    def setUp(self):
        """Set up test fixtures."""
        self.discipline = Discipline.objects.create(
            name="Test Combat", slug="test-combat"
        )
        self.combatant = Combatant.objects.create(
            sca_name="Test Fighter",
            legal_name="Test Legal",
            email="test@example.com",
            accepted_privacy_policy=True,
        )

    @override_settings(REMINDER_DAYS=[60, 30, 14, 0])
    def test_card_creation_creates_reminders(self):
        """Creating a card triggers reminder creation."""
        card = Card.objects.create(
            combatant=self.combatant,
            discipline=self.discipline,
            date_issued=today(),
        )

        reminders = Reminder.objects.filter(object_id=card.id)
        self.assertEqual(reminders.count(), 4)

    @override_settings(REMINDER_DAYS=[60, 30, 14, 0])
    def test_card_date_change_updates_reminders(self):
        """Changing date_issued recreates reminders."""
        card = Card.objects.create(
            combatant=self.combatant,
            discipline=self.discipline,
            date_issued=today() - timedelta(days=100),
        )
        old_due_dates = list(
            Reminder.objects.filter(object_id=card.id).values_list(
                "due_date", flat=True
            )
        )

        card.date_issued = today()
        card.save()

        new_due_dates = list(
            Reminder.objects.filter(object_id=card.id).values_list(
                "due_date", flat=True
            )
        )
        self.assertNotEqual(old_due_dates, new_due_dates)

    @override_settings(REMINDER_DAYS=[60, 30, 14, 0])
    def test_card_other_field_change_no_reminder_update(self):
        """Changing non-date fields doesn't recreate reminders."""
        card = Card.objects.create(
            combatant=self.combatant,
            discipline=self.discipline,
            date_issued=today(),
        )
        old_reminder_ids = set(
            Reminder.objects.filter(object_id=card.id).values_list("id", flat=True)
        )

        card.save()

        new_reminder_ids = set(
            Reminder.objects.filter(object_id=card.id).values_list("id", flat=True)
        )
        self.assertEqual(old_reminder_ids, new_reminder_ids)


class WaiverReminderSignalTestCase(TestCase):
    """Tests for Waiver post_save signal creating reminders."""

    def setUp(self):
        """Set up test fixtures."""
        self.combatant = Combatant.objects.create(
            sca_name="Test Fighter",
            legal_name="Test Legal",
            email="test@example.com",
            accepted_privacy_policy=True,
        )

    @override_settings(REMINDER_DAYS=[60, 30, 14, 0])
    def test_waiver_creation_creates_reminders(self):
        """Creating a waiver triggers reminder creation."""
        waiver = Waiver.objects.create(
            combatant=self.combatant,
            date_signed=today(),
        )

        reminders = Reminder.objects.filter(object_id=waiver.id)
        self.assertEqual(reminders.count(), 4)

    @override_settings(REMINDER_DAYS=[60, 30, 14, 0])
    def test_waiver_date_change_updates_reminders(self):
        """Changing date_signed recreates reminders."""
        waiver = Waiver.objects.create(
            combatant=self.combatant,
            date_signed=today() - timedelta(days=100),
        )
        old_due_dates = list(
            Reminder.objects.filter(object_id=waiver.id).values_list(
                "due_date", flat=True
            )
        )

        waiver.date_signed = today()
        waiver.save()

        new_due_dates = list(
            Reminder.objects.filter(object_id=waiver.id).values_list(
                "due_date", flat=True
            )
        )
        self.assertNotEqual(old_due_dates, new_due_dates)


class SendRemindersEmailFailureTestCase(TestCase):
    """Tests for send_reminders behavior when emails fail."""

    def setUp(self):
        """Set up test fixtures."""
        self.discipline = Discipline.objects.create(
            name="Test Combat", slug="test-combat"
        )
        self.combatant = Combatant.objects.create(
            sca_name="Test Fighter",
            legal_name="Test Legal",
            email="test@example.com",
            accepted_privacy_policy=True,
        )

    @override_settings(REMINDER_DAYS=[60, 30, 14, 0])
    @patch("cards.models.card.send_card_reminder")
    @patch("cards.models.card.send_card_expiry")
    def test_reminders_kept_on_email_failure(self, mock_expiry, mock_reminder):
        """Reminders are kept when email sending fails."""
        mock_reminder.return_value = False
        mock_expiry.return_value = False
        card = Card.objects.create(
            combatant=self.combatant,
            discipline=self.discipline,
            date_issued=today() - timedelta(days=365 * 2 - 30),
        )
        card_ct = ContentType.objects.get_for_model(Card)
        Reminder.objects.filter(content_type=card_ct, object_id=card.id).update(
            due_date=today()
        )
        initial_count = Reminder.objects.filter(
            content_type=card_ct, object_id=card.id
        ).count()

        call_command("send_reminders")

        final_count = Reminder.objects.filter(
            content_type=card_ct, object_id=card.id
        ).count()
        self.assertEqual(initial_count, final_count)

    @override_settings(REMINDER_DAYS=[60, 30, 14, 0])
    @patch("cards.models.card.send_card_reminder")
    @patch("cards.models.card.send_card_expiry")
    def test_reminders_deleted_on_email_success(self, mock_expiry, mock_reminder):
        """Reminders are deleted when email sending succeeds."""
        mock_reminder.return_value = True
        mock_expiry.return_value = True
        card = Card.objects.create(
            combatant=self.combatant,
            discipline=self.discipline,
            date_issued=today() - timedelta(days=365 * 2 - 30),
        )
        card_ct = ContentType.objects.get_for_model(Card)
        Reminder.objects.filter(content_type=card_ct, object_id=card.id).update(
            due_date=today()
        )

        call_command("send_reminders")

        final_count = Reminder.objects.filter(
            content_type=card_ct, object_id=card.id
        ).count()
        self.assertEqual(final_count, 0)


class ReminderHygieneCommandTestCase(TestCase):
    """Tests for the reminder_hygiene management command."""

    def setUp(self):
        """Set up test fixtures."""
        self.discipline = Discipline.objects.create(
            name="Test Combat", slug="test-combat"
        )
        self.combatant = Combatant.objects.create(
            sca_name="Test Fighter",
            legal_name="Test Legal",
            email="test@example.com",
            accepted_privacy_policy=True,
        )

    @override_settings(REMINDER_DAYS=[60, 30, 14, 0])
    def test_hygiene_reports_missing_reminders(self):
        """Hygiene command reports cards with missing reminders."""
        card = Card.objects.create(
            combatant=self.combatant,
            discipline=self.discipline,
            date_issued=today(),
        )
        Reminder.objects.filter(object_id=card.id).delete()

        call_command("reminder_hygiene")

    @override_settings(REMINDER_DAYS=[60, 30, 14, 0])
    def test_hygiene_fix_creates_missing_reminders(self):
        """Hygiene command with --fix creates missing reminders."""
        card = Card.objects.create(
            combatant=self.combatant,
            discipline=self.discipline,
            date_issued=today(),
        )
        Reminder.objects.filter(object_id=card.id).delete()
        self.assertEqual(Reminder.objects.filter(object_id=card.id).count(), 0)

        call_command("reminder_hygiene", "--fix")

        self.assertEqual(Reminder.objects.filter(object_id=card.id).count(), 4)

    @override_settings(REMINDER_DAYS=[60, 30, 14, 0])
    def test_hygiene_reports_orphaned_reminders(self):
        """Hygiene command reports orphaned reminders."""
        card_ct = ContentType.objects.get_for_model(Card)
        Reminder.objects.create(
            content_type=card_ct,
            object_id=99999,
            days_to_expiry=30,
            due_date=today(),
        )

        call_command("reminder_hygiene")

    @override_settings(REMINDER_DAYS=[60, 30, 14, 0])
    def test_hygiene_no_issues_with_healthy_data(self):
        """Hygiene command reports no issues when data is healthy."""
        Card.objects.create(
            combatant=self.combatant,
            discipline=self.discipline,
            date_issued=today(),
        )

        call_command("reminder_hygiene")

    @override_settings(REMINDER_DAYS=[60, 30, 14, 0])
    def test_hygiene_ignores_expired_cards(self):
        """Hygiene command ignores expired cards."""
        expired_card = Card.objects.create(
            combatant=self.combatant,
            discipline=self.discipline,
            date_issued=today() - timedelta(days=365 * 3),
        )
        Reminder.objects.filter(object_id=expired_card.id).delete()

        call_command("reminder_hygiene", "--fix")

        self.assertEqual(Reminder.objects.filter(object_id=expired_card.id).count(), 0)

    @override_settings(REMINDER_DAYS=[60, 30, 14, 0])
    def test_hygiene_checks_waivers(self):
        """Hygiene command checks waivers too."""
        waiver = Waiver.objects.create(
            combatant=self.combatant,
            date_signed=today(),
        )
        Reminder.objects.filter(object_id=waiver.id).delete()

        call_command("reminder_hygiene", "--fix")

        waiver_ct = ContentType.objects.get_for_model(Waiver)
        waiver_reminders = Reminder.objects.filter(
            content_type=waiver_ct, object_id=waiver.id
        )
        self.assertEqual(waiver_reminders.count(), 4)
