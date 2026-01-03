"""Tests for PIN views."""

from datetime import timedelta

from cards.models import Combatant, OneTimeCode, Waiver
from cards.utility.time import today
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from feature_switches.models import (
    ACCESS_MODE_DISABLED,
    ACCESS_MODE_GLOBAL,
    ACCESS_MODE_LIST,
    FeatureSwitch,
)


class PINSetupViewTestCase(TestCase):
    """Tests for PIN setup view."""

    def setUp(self):
        """Set up test data."""
        self.combatant = Combatant.objects.create(
            sca_name="Test Fighter",
            legal_name="Test Legal",
            email="test@example.com",
            accepted_privacy_policy=True,
            card_id="setup-test-card",
        )
        self.one_time_code = OneTimeCode.objects.create(
            combatant=self.combatant,
            url_template="/pin/setup/{code}",
        )
        FeatureSwitch.objects.create(
            name="pin_authentication", access_mode=ACCESS_MODE_GLOBAL
        )

    def test_get_setup_page(self):
        """Test GET request returns setup form."""
        response = self.client.get(
            reverse("pin-setup", args=[str(self.one_time_code.code)])
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Set Your PIN")
        self.assertContains(response, self.combatant.name)

    def test_get_invalid_code(self):
        """Test GET with invalid code shows error."""
        response = self.client.get(reverse("pin-setup", args=["invalid-code"]))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "invalid or has expired")

    def test_get_expired_code(self):
        """Test GET with expired code shows error."""
        self.one_time_code.expires_at = timezone.now() - timedelta(hours=1)
        self.one_time_code.save()

        response = self.client.get(
            reverse("pin-setup", args=[str(self.one_time_code.code)])
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "expired or already been used")

    def test_get_consumed_code(self):
        """Test GET with consumed code shows error."""
        self.one_time_code.consumed = True
        self.one_time_code.save()

        response = self.client.get(
            reverse("pin-setup", args=[str(self.one_time_code.code)])
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "expired or already been used")

    def test_post_valid_pin(self):
        """Test POST with valid PIN sets the PIN and shows privacy accepted page."""
        response = self.client.post(
            reverse("pin-setup", args=[str(self.one_time_code.code)]),
            {"pin": "1234", "pin_confirm": "1234"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "home/registration_completed.html")
        self.assertContains(response, "Welcome!")
        self.assertContains(response, self.combatant.card_url)
        self.assertContains(response, "sent you an email")

        self.combatant.refresh_from_db()
        self.assertTrue(self.combatant.has_pin)
        self.assertTrue(self.combatant.check_pin("1234"))

        self.one_time_code.refresh_from_db()
        self.assertTrue(self.one_time_code.consumed)

    def test_post_mismatched_pins(self):
        """Test POST with mismatched PINs shows error."""
        response = self.client.post(
            reverse("pin-setup", args=[str(self.one_time_code.code)]),
            {"pin": "1234", "pin_confirm": "5678"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "PINs do not match")

        self.combatant.refresh_from_db()
        self.assertFalse(self.combatant.has_pin)

    def test_post_invalid_pin_format(self):
        """Test POST with invalid PIN format shows error."""
        response = self.client.post(
            reverse("pin-setup", args=[str(self.one_time_code.code)]),
            {"pin": "abc", "pin_confirm": "abc"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "4-6 numeric digits")

    def test_feature_disabled_shows_expired_message(self):
        """Test that disabled feature shows expired message (transparent to user)."""
        FeatureSwitch.objects.filter(name="pin_authentication").update(
            access_mode=ACCESS_MODE_DISABLED
        )

        response = self.client.get(
            reverse("pin-setup", args=[str(self.one_time_code.code)])
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "expired or already been used")

    def test_list_mode_combatant_in_list_allows_setup(self):
        """Test that combatant in list can access PIN setup."""
        switch = FeatureSwitch.objects.filter(name="pin_authentication").first()
        switch.access_mode = ACCESS_MODE_LIST
        switch.save()
        switch.allowed_users.add(self.combatant)

        response = self.client.get(
            reverse("pin-setup", args=[str(self.one_time_code.code)])
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Set Your PIN")

    def test_list_mode_combatant_not_in_list_shows_expired(self):
        """Test that combatant not in list sees expired message."""
        switch = FeatureSwitch.objects.filter(name="pin_authentication").first()
        switch.access_mode = ACCESS_MODE_LIST
        switch.save()

        response = self.client.get(
            reverse("pin-setup", args=[str(self.one_time_code.code)])
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "expired or already been used")


class PINResetViewTestCase(TestCase):
    """Tests for PIN reset view."""

    def setUp(self):
        """Set up test data."""
        self.combatant = Combatant.objects.create(
            sca_name="Test Fighter",
            legal_name="Test Legal",
            email="test@example.com",
            accepted_privacy_policy=True,
            card_id="reset-test-card",
        )
        self.combatant.set_pin("9999")
        self.one_time_code = OneTimeCode.objects.create(
            combatant=self.combatant,
            url_template="/pin/reset/{code}",
        )
        FeatureSwitch.objects.create(
            name="pin_authentication", access_mode=ACCESS_MODE_GLOBAL
        )

    def test_get_reset_page(self):
        """Test GET request returns reset form."""
        response = self.client.get(
            reverse("pin-reset", args=[str(self.one_time_code.code)])
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Reset Your PIN")

    def test_post_valid_new_pin(self):
        """Test POST with valid PIN resets the PIN and shows privacy accepted page."""
        response = self.client.post(
            reverse("pin-reset", args=[str(self.one_time_code.code)]),
            {"pin": "5678", "pin_confirm": "5678"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "home/registration_completed.html")
        self.assertContains(response, "PIN Updated")
        self.assertContains(response, self.combatant.card_url)
        self.assertNotContains(response, "sent you an email")

        self.combatant.refresh_from_db()
        self.assertTrue(self.combatant.check_pin("5678"))
        self.assertFalse(self.combatant.check_pin("9999"))


class PINVerifyViewTestCase(TestCase):
    """Tests for PIN verify view."""

    def setUp(self):
        """Set up test data."""
        self.combatant = Combatant.objects.create(
            sca_name="Test Fighter",
            legal_name="Test Legal",
            email="test@example.com",
            accepted_privacy_policy=True,
            card_id="test-card-123",
        )
        self.combatant.set_pin("1234")
        FeatureSwitch.objects.create(
            name="pin_authentication", access_mode=ACCESS_MODE_GLOBAL
        )

    def test_get_verify_page(self):
        """Test GET request returns verify form."""
        response = self.client.get(reverse("pin-verify", args=["test-card-123"]))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Enter Your PIN")

    def test_post_correct_pin_redirects(self):
        """Test POST with correct PIN redirects to card."""
        response = self.client.post(
            reverse("pin-verify", args=["test-card-123"]),
            {"pin": "1234"},
        )

        self.assertRedirects(
            response,
            reverse("combatant-card", args=["test-card-123"]),
            fetch_redirect_response=False,
        )

    def test_post_correct_pin_sets_session(self):
        """Test POST with correct PIN sets session verification."""
        self.client.post(
            reverse("pin-verify", args=["test-card-123"]),
            {"pin": "1234"},
        )

        session = self.client.session
        self.assertTrue(session.get("pin_verified_test-card-123"))

    def test_post_incorrect_pin_shows_error(self):
        """Test POST with incorrect PIN shows error."""
        response = self.client.post(
            reverse("pin-verify", args=["test-card-123"]),
            {"pin": "9999"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Incorrect PIN")

    def test_post_incorrect_pin_shows_remaining_attempts(self):
        """Test that remaining attempts are shown."""
        response = self.client.post(
            reverse("pin-verify", args=["test-card-123"]),
            {"pin": "9999"},
        )

        self.assertContains(response, "attempts remaining")

    def test_lockout_shows_message(self):
        """Test that locked out account shows appropriate message."""
        self.combatant.pin_locked_until = timezone.now() + timedelta(minutes=10)
        self.combatant.save()

        response = self.client.get(reverse("pin-verify", args=["test-card-123"]))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "temporarily locked")

    def test_no_pin_set_redirects_to_card(self):
        """Test that combatant without PIN is redirected to card."""
        self.combatant.clear_pin()

        response = self.client.get(reverse("pin-verify", args=["test-card-123"]))

        self.assertRedirects(
            response,
            reverse("combatant-card", args=["test-card-123"]),
            fetch_redirect_response=False,
        )

    def test_feature_disabled_redirects_to_card(self):
        """Test that disabled feature redirects to card."""
        FeatureSwitch.objects.filter(name="pin_authentication").update(
            access_mode=ACCESS_MODE_DISABLED
        )

        response = self.client.get(reverse("pin-verify", args=["test-card-123"]))

        self.assertRedirects(
            response,
            reverse("combatant-card", args=["test-card-123"]),
            fetch_redirect_response=False,
        )

    def test_nonexistent_card_shows_error(self):
        """Test that nonexistent card shows error."""
        response = self.client.get(reverse("pin-verify", args=["nonexistent"]))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Card not found")


class CombatantCardWithPINTestCase(TestCase):
    """Tests for combatant card view with PIN protection."""

    def setUp(self):
        """Set up test data."""
        self.combatant = Combatant.objects.create(
            sca_name="Test Fighter",
            legal_name="Test Legal",
            email="test@example.com",
            accepted_privacy_policy=True,
            card_id="protected-card",
        )

        Waiver.objects.create(
            combatant=self.combatant,
            date_signed=today(),
        )
        FeatureSwitch.objects.create(
            name="pin_authentication", access_mode=ACCESS_MODE_GLOBAL
        )

    def test_card_without_pin_accessible(self):
        """Test that card without PIN set is directly accessible."""
        response = self.client.get(reverse("combatant-card", args=["protected-card"]))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Test Fighter")

    def test_card_with_pin_requires_verification(self):
        """Test that card with PIN redirects to verify."""
        self.combatant.set_pin("1234")

        response = self.client.get(reverse("combatant-card", args=["protected-card"]))

        self.assertRedirects(
            response,
            reverse("pin-verify", args=["protected-card"]),
            fetch_redirect_response=False,
        )

    def test_card_accessible_after_verification(self):
        """Test that card is accessible after PIN verification."""
        self.combatant.set_pin("1234")

        session = self.client.session
        session["pin_verified_protected-card"] = True
        session.save()

        response = self.client.get(reverse("combatant-card", args=["protected-card"]))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Test Fighter")

    def test_feature_disabled_card_accessible(self):
        """Test that card is accessible when feature is disabled."""
        self.combatant.set_pin("1234")
        FeatureSwitch.objects.filter(name="pin_authentication").update(
            access_mode=ACCESS_MODE_DISABLED
        )

        response = self.client.get(reverse("combatant-card", args=["protected-card"]))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Test Fighter")
