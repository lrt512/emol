from datetime import datetime, timedelta
from unittest.mock import patch

from cards.models.authorization import Authorization
from cards.models.combatant import Combatant
from cards.models.discipline import Discipline
from cards.models.one_time_code import OneTimeCode
from django.db.utils import IntegrityError
from django.test import TestCase, override_settings
from django.utils import timezone


class CombatantModelTestCase(TestCase):
    def setUp(self):
        self.discipline = Discipline.objects.create(name="Fencing")
        self.authorization = Authorization.objects.create(
            name="Heavy Rapier", discipline=self.discipline, is_primary=True
        )
        self.combatant = Combatant.objects.create(
            sca_name="John the Blue", legal_name="John Smith"
        )

    def test_combatant_with_no_legal_name(self):
        self.combatant.legal_name = None
        with self.assertRaises(IntegrityError):
            self.combatant.save()

    def test_combatant_waiver_date(self):
        self.combatant.waiver_date = datetime(2018, 1, 1)
        self.combatant.save()
        assert (
            self.combatant.waiver_expires
            == self.combatant.waiver_date + self.combatant.waiver_duration
        )

    def test_combatant_privacy_policy_code(self):
        assert self.combatant.privacy_policy_code == "JtB"


class CombatantPINTestCase(TestCase):
    """Tests for Combatant PIN authentication methods."""

    def setUp(self):
        """Set up test combatant."""
        self.combatant = Combatant.objects.create(
            sca_name="Test Fighter",
            legal_name="Test Legal",
            email="test@example.com",
            accepted_privacy_policy=True,
        )

    def test_has_pin_false_when_no_pin_set(self):
        """Test has_pin returns False when no PIN is set."""
        self.assertFalse(self.combatant.has_pin)

    def test_has_pin_true_when_pin_set(self):
        """Test has_pin returns True after PIN is set."""
        self.combatant.set_pin("1234")
        self.assertTrue(self.combatant.has_pin)

    def test_set_pin_valid_4_digits(self):
        """Test setting a 4-digit PIN."""
        result = self.combatant.set_pin("1234")
        self.assertTrue(result)
        self.assertTrue(self.combatant.has_pin)

    def test_set_pin_valid_5_digits(self):
        """Test setting a 5-digit PIN."""
        result = self.combatant.set_pin("12345")
        self.assertTrue(result)

    def test_set_pin_valid_6_digits(self):
        """Test setting a 6-digit PIN."""
        result = self.combatant.set_pin("123456")
        self.assertTrue(result)

    def test_set_pin_invalid_3_digits(self):
        """Test that 3-digit PIN is rejected."""
        with self.assertRaises(ValueError) as ctx:
            self.combatant.set_pin("123")
        self.assertIn("4-6 numeric digits", str(ctx.exception))

    def test_set_pin_invalid_7_digits(self):
        """Test that 7-digit PIN is rejected."""
        with self.assertRaises(ValueError):
            self.combatant.set_pin("1234567")

    def test_set_pin_invalid_letters(self):
        """Test that PIN with letters is rejected."""
        with self.assertRaises(ValueError):
            self.combatant.set_pin("12ab")

    def test_set_pin_invalid_empty(self):
        """Test that empty PIN is rejected."""
        with self.assertRaises(ValueError):
            self.combatant.set_pin("")

    def test_set_pin_invalid_none(self):
        """Test that None PIN is rejected."""
        with self.assertRaises(ValueError):
            self.combatant.set_pin(None)

    def test_check_pin_correct(self):
        """Test checking correct PIN returns True."""
        self.combatant.set_pin("1234")
        result = self.combatant.check_pin("1234")
        self.assertTrue(result)

    def test_check_pin_incorrect(self):
        """Test checking incorrect PIN returns False."""
        self.combatant.set_pin("1234")
        result = self.combatant.check_pin("5678")
        self.assertFalse(result)

    def test_check_pin_no_pin_set(self):
        """Test checking PIN when none is set returns False."""
        result = self.combatant.check_pin("1234")
        self.assertFalse(result)

    def test_check_pin_increments_failed_attempts(self):
        """Test that failed PIN attempts are counted."""
        self.combatant.set_pin("1234")
        self.assertEqual(self.combatant.pin_failed_attempts, 0)

        self.combatant.check_pin("wrong")
        self.combatant.refresh_from_db()
        self.assertEqual(self.combatant.pin_failed_attempts, 1)

    def test_check_pin_resets_attempts_on_success(self):
        """Test that successful PIN check resets failed attempts."""
        self.combatant.set_pin("1234")
        self.combatant.check_pin("wrong")
        self.combatant.check_pin("wrong")
        self.combatant.refresh_from_db()
        self.assertEqual(self.combatant.pin_failed_attempts, 2)

        self.combatant.check_pin("1234")
        self.combatant.refresh_from_db()
        self.assertEqual(self.combatant.pin_failed_attempts, 0)

    def test_lockout_after_max_attempts(self):
        """Test that account is locked after max failed attempts."""
        self.combatant.set_pin("1234")

        for _ in range(Combatant.PIN_MAX_ATTEMPTS):
            self.combatant.check_pin("wrong")

        self.combatant.refresh_from_db()
        self.assertTrue(self.combatant.is_locked_out)
        self.assertIsNotNone(self.combatant.pin_locked_until)

    def test_is_locked_out_false_initially(self):
        """Test that is_locked_out is False initially."""
        self.assertFalse(self.combatant.is_locked_out)

    def test_is_locked_out_true_during_lockout(self):
        """Test that is_locked_out returns True during lockout period."""
        self.combatant.pin_locked_until = timezone.now() + timedelta(minutes=10)
        self.combatant.save()
        self.assertTrue(self.combatant.is_locked_out)

    def test_is_locked_out_false_after_lockout_expires(self):
        """Test that is_locked_out returns False after lockout expires."""
        self.combatant.pin_locked_until = timezone.now() - timedelta(minutes=1)
        self.combatant.save()
        self.assertFalse(self.combatant.is_locked_out)

    def test_check_pin_fails_during_lockout(self):
        """Test that PIN check fails during lockout even with correct PIN."""
        self.combatant.set_pin("1234")
        self.combatant.pin_locked_until = timezone.now() + timedelta(minutes=10)
        self.combatant.save()

        result = self.combatant.check_pin("1234")
        self.assertFalse(result)

    def test_clear_lockout(self):
        """Test that clear_lockout resets lockout state."""
        self.combatant.pin_failed_attempts = 5
        self.combatant.pin_locked_until = timezone.now() + timedelta(minutes=10)
        self.combatant.save()

        self.combatant.clear_lockout()

        self.combatant.refresh_from_db()
        self.assertEqual(self.combatant.pin_failed_attempts, 0)
        self.assertIsNone(self.combatant.pin_locked_until)
        self.assertFalse(self.combatant.is_locked_out)

    def test_clear_pin(self):
        """Test that clear_pin removes PIN and resets lockout."""
        self.combatant.set_pin("1234")
        self.combatant.pin_failed_attempts = 3
        self.combatant.save()

        self.combatant.clear_pin()

        self.combatant.refresh_from_db()
        self.assertFalse(self.combatant.has_pin)
        self.assertIsNone(self.combatant.pin_hash)
        self.assertEqual(self.combatant.pin_failed_attempts, 0)

    @patch("cards.models.combatant.send_pin_lockout_notification")
    def test_lockout_sends_notification(self, mock_send):
        """Test that lockout triggers email notification."""
        self.combatant.set_pin("1234")

        for _ in range(Combatant.PIN_MAX_ATTEMPTS):
            self.combatant.check_pin("wrong")

        mock_send.assert_called_once_with(self.combatant)

    @override_settings(BASE_URL="http://test.example.com")
    def test_initiate_pin_reset(self):
        """Test initiating PIN reset creates OneTimeCode and clears PIN."""
        self.combatant.set_pin("1234")

        one_time_code = self.combatant.initiate_pin_reset()

        self.combatant.refresh_from_db()
        self.assertFalse(self.combatant.has_pin)
        self.assertIsInstance(one_time_code, OneTimeCode)
        self.assertEqual(one_time_code.combatant, self.combatant)
        self.assertIn("/pin/reset/", one_time_code.url_template)


class CombatantEmailNonUniqueTestCase(TestCase):
    """Tests for non-unique email field on Combatant."""

    def test_multiple_combatants_same_email(self):
        """Test that multiple combatants can share the same email."""
        combatant1 = Combatant.objects.create(
            sca_name="Fighter One",
            legal_name="Legal One",
            email="shared@example.com",
        )
        combatant2 = Combatant.objects.create(
            sca_name="Fighter Two",
            legal_name="Legal Two",
            email="shared@example.com",
        )

        self.assertEqual(combatant1.email, combatant2.email)
        self.assertNotEqual(combatant1.id, combatant2.id)

    def test_filter_by_email_returns_multiple(self):
        """Test that filtering by email returns all matching combatants."""
        Combatant.objects.create(
            sca_name="Fighter One",
            legal_name="Legal One",
            email="family@example.com",
        )
        Combatant.objects.create(
            sca_name="Fighter Two",
            legal_name="Legal Two",
            email="family@example.com",
        )
        Combatant.objects.create(
            sca_name="Fighter Three",
            legal_name="Legal Three",
            email="other@example.com",
        )

        family_combatants = Combatant.objects.filter(email="family@example.com")
        self.assertEqual(family_combatants.count(), 2)
