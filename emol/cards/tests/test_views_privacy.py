"""Tests for privacy-related views."""

from django.test import TestCase, override_settings
from django.urls import reverse

from cards.models import Combatant, PrivacyPolicy


class PrivacyPolicyViewTestCase(TestCase):
    """Tests for the privacy policy view."""

    def setUp(self):
        """Set up test fixtures."""
        PrivacyPolicy.objects.create(text="# Test Privacy Policy\n\nThis is a test.")
        self.combatant = Combatant.objects.create(
            sca_name="Test Fighter",
            legal_name="Test Legal",
            email="test@example.com",
            accepted_privacy_policy=False,
        )

    def test_privacy_policy_get_without_code(self):
        """GET request without code shows policy."""
        response = self.client.get(reverse("privacy-policy"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Test Privacy Policy")

    def test_privacy_policy_get_with_valid_code(self):
        """GET request with valid code shows policy with accept form."""
        code = self.combatant.privacy_acceptance_code
        response = self.client.get(
            reverse("privacy-policy", kwargs={"code": code})
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Test Privacy Policy")

    def test_privacy_policy_get_with_invalid_code(self):
        """GET request with invalid code returns 404."""
        response = self.client.get(
            reverse("privacy-policy", kwargs={"code": "invalid"})
        )
        self.assertEqual(response.status_code, 404)

    @override_settings(SEND_EMAIL=False, SITE_URL="http://test.example.com")
    def test_privacy_policy_accept(self):
        """POST with accept updates combatant and shows accepted page."""
        code = self.combatant.privacy_acceptance_code
        response = self.client.post(
            reverse("privacy-policy", kwargs={"code": code}),
            {"code": code, "accept": "1"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "privacy/privacy_accepted.html")
        self.combatant.refresh_from_db()
        self.assertTrue(self.combatant.accepted_privacy_policy)

    def test_privacy_policy_decline(self):
        """POST with decline deletes combatant."""
        code = self.combatant.privacy_acceptance_code
        combatant_id = self.combatant.id
        response = self.client.post(
            reverse("privacy-policy", kwargs={"code": code}),
            {"code": code, "decline": "1"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "privacy/privacy_declined.html")
        self.assertFalse(Combatant.objects.filter(id=combatant_id).exists())
