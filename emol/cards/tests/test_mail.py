"""Tests for email sending functions."""

from datetime import timedelta
from unittest.mock import patch

from django.contrib.contenttypes.models import ContentType
from django.test import TestCase, override_settings

from cards.mail import (
    send_card_expiry,
    send_card_reminder,
    send_card_url,
    send_info_update,
    send_privacy_policy,
    send_waiver_expiry,
    send_waiver_reminder,
)
from cards.models import Card, Combatant, Discipline, Reminder, UpdateCode, Waiver
from cards.utility.time import today


class SendCardReminderTestCase(TestCase):
    """Tests for send_card_reminder."""

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
        self.card = Card.objects.create(
            combatant=self.combatant,
            discipline=self.discipline,
            date_issued=today(),
        )

    @override_settings(SEND_EMAIL=False)
    def test_send_card_reminder_success(self):
        """send_card_reminder sends email and returns True."""
        reminder = Reminder.objects.filter(
            content_type=ContentType.objects.get_for_model(Card),
            object_id=self.card.id,
            days_to_expiry=30,
        ).first()

        result = send_card_reminder(reminder)

        self.assertTrue(result)

    @override_settings(SEND_EMAIL=False)
    def test_send_card_reminder_with_invalid_reminder_returns_false(self):
        """send_card_reminder returns False for orphaned reminder."""
        card_ct = ContentType.objects.get_for_model(Card)
        orphaned = Reminder.objects.create(
            content_type=card_ct,
            object_id=99999,
            days_to_expiry=30,
            due_date=today(),
        )

        result = send_card_reminder(orphaned)

        self.assertFalse(result)


class SendCardExpiryTestCase(TestCase):
    """Tests for send_card_expiry."""

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
        self.card = Card.objects.create(
            combatant=self.combatant,
            discipline=self.discipline,
            date_issued=today(),
        )

    @override_settings(SEND_EMAIL=False)
    def test_send_card_expiry_success(self):
        """send_card_expiry sends email and returns True."""
        reminder = Reminder.objects.filter(
            content_type=ContentType.objects.get_for_model(Card),
            object_id=self.card.id,
            days_to_expiry=0,
        ).first()

        result = send_card_expiry(reminder)

        self.assertTrue(result)


class SendWaiverReminderTestCase(TestCase):
    """Tests for send_waiver_reminder."""

    def setUp(self):
        """Set up test fixtures."""
        self.combatant = Combatant.objects.create(
            sca_name="Test Fighter",
            legal_name="Test Legal",
            email="test@example.com",
            accepted_privacy_policy=True,
        )
        self.waiver = Waiver.objects.create(
            combatant=self.combatant,
            date_signed=today(),
        )

    @override_settings(SEND_EMAIL=False)
    def test_send_waiver_reminder_success(self):
        """send_waiver_reminder sends email and returns True."""
        reminder = Reminder.objects.filter(
            content_type=ContentType.objects.get_for_model(Waiver),
            object_id=self.waiver.id,
            days_to_expiry=30,
        ).first()

        result = send_waiver_reminder(reminder)

        self.assertTrue(result)


class SendWaiverExpiryTestCase(TestCase):
    """Tests for send_waiver_expiry."""

    def setUp(self):
        """Set up test fixtures."""
        self.combatant = Combatant.objects.create(
            sca_name="Test Fighter",
            legal_name="Test Legal",
            email="test@example.com",
            accepted_privacy_policy=True,
        )
        self.waiver = Waiver.objects.create(
            combatant=self.combatant,
            date_signed=today(),
        )

    @override_settings(SEND_EMAIL=False)
    def test_send_waiver_expiry_success(self):
        """send_waiver_expiry sends email and returns True."""
        reminder = Reminder.objects.filter(
            content_type=ContentType.objects.get_for_model(Waiver),
            object_id=self.waiver.id,
            days_to_expiry=0,
        ).first()

        result = send_waiver_expiry(reminder)

        self.assertTrue(result)


class SendInfoUpdateTestCase(TestCase):
    """Tests for send_info_update."""

    def setUp(self):
        """Set up test fixtures."""
        self.combatant = Combatant.objects.create(
            sca_name="Test Fighter",
            legal_name="Test Legal",
            email="test@example.com",
            accepted_privacy_policy=True,
        )

    @override_settings(SEND_EMAIL=False)
    def test_send_info_update_success(self):
        """send_info_update sends email and returns True."""
        update_code = UpdateCode.objects.create(combatant=self.combatant)

        result = send_info_update(self.combatant, update_code)

        self.assertTrue(result)


class SendCardUrlTestCase(TestCase):
    """Tests for send_card_url."""

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
            card_id="TEST123",
        )
        self.card = Card.objects.create(
            combatant=self.combatant,
            discipline=self.discipline,
            date_issued=today(),
        )

    @override_settings(SEND_EMAIL=False, BASE_URL="http://test.example.com")
    def test_send_card_url_success(self):
        """send_card_url sends email and returns True."""
        result = send_card_url(self.combatant)

        self.assertTrue(result)


class SendPrivacyPolicyTestCase(TestCase):
    """Tests for send_privacy_policy."""

    def setUp(self):
        """Set up test fixtures."""
        self.combatant = Combatant.objects.create(
            sca_name="Test Fighter",
            legal_name="Test Legal",
            email="test@example.com",
            accepted_privacy_policy=False,
        )

    @override_settings(SEND_EMAIL=False, SITE_URL="http://test.example.com")
    def test_send_privacy_policy_success(self):
        """send_privacy_policy sends email and returns True."""
        result = send_privacy_policy(self.combatant)

        self.assertTrue(result)

