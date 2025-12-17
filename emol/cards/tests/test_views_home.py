from unittest.mock import patch

from cards.models import Combatant, OneTimeCode
from django.test import TestCase
from django.urls import reverse


class HomeViewsTestCase(TestCase):
    """Test the home view functions"""

    def setUp(self):
        """Set up test data"""
        # Create combatants for testing
        self.combatant_with_privacy = Combatant.objects.create(
            sca_name="Test Fighter",
            legal_name="Test Legal",
            email="test@example.com",
            accepted_privacy_policy=True,
        )

        self.combatant_without_privacy = Combatant.objects.create(
            sca_name="Test Fighter 2",
            legal_name="Test Legal 2",
            email="test2@example.com",
            accepted_privacy_policy=False,
        )

    def test_request_card_get(self):
        """Test GET request to request_card view"""
        response = self.client.get(reverse("request-card"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Enter your email address")

    @patch("cards.views.home.send_card_url")
    def test_request_card_post_existing_combatant_with_privacy(
        self, mock_send_card_url
    ):
        """Test POST request for existing combatant who accepted privacy policy"""
        response = self.client.post(
            reverse("request-card"), {"request-card-email": "test@example.com"}
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response,
            "If a combatant exists for this email, instructions have been sent.",
        )
        mock_send_card_url.assert_called_once_with(self.combatant_with_privacy)

    @patch("cards.views.home.send_privacy_policy")
    def test_request_card_post_existing_combatant_without_privacy(
        self, mock_send_privacy_policy
    ):
        """Test POST request for combatant who hasn't accepted privacy policy"""
        response = self.client.post(
            reverse("request-card"), {"request-card-email": "test2@example.com"}
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response,
            "If a combatant exists for this email, instructions have been sent.",
        )
        mock_send_privacy_policy.assert_called_once_with(self.combatant_without_privacy)

    def test_request_card_post_nonexistent_combatant(self):
        """Test POST request for non-existent combatant"""
        response = self.client.post(
            reverse("request-card"), {"request-card-email": "nonexistent@example.com"}
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response,
            "If a combatant exists for this email, instructions have been sent.",
        )

    def test_request_card_post_no_email(self):
        """Test POST request with no email provided"""
        response = self.client.post(reverse("request-card"), {})

        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response,
            "If a combatant exists for this email, instructions have been sent.",
        )

    def test_update_info_get(self):
        """Test GET request to update_info view"""
        response = self.client.get(reverse("update-info"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Enter your email address")

    @patch("cards.views.home.send_info_update")
    def test_update_info_post_existing_combatant_with_privacy(
        self, mock_send_info_update
    ):
        """Test POST request for existing combatant who accepted privacy policy"""
        response = self.client.post(
            reverse("update-info"), {"update-info-email": "test@example.com"}
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response, "If a combatant with this email exists, an email has been sent"
        )

        # Verify an OneTimeCode was created
        one_time_code = OneTimeCode.objects.get(combatant=self.combatant_with_privacy)
        mock_send_info_update.assert_called_once_with(
            self.combatant_with_privacy, one_time_code
        )

    @patch("cards.views.home.send_info_update")
    def test_update_info_post_creates_new_code(self, mock_send_info_update):
        """Test POST request always creates a new OneTimeCode"""
        # Create an existing OneTimeCode
        existing_code = OneTimeCode.objects.create(
            combatant=self.combatant_with_privacy,
            url_template="/self-serve-update/{code}",
        )

        response = self.client.post(
            reverse("update-info"), {"update-info-email": "test@example.com"}
        )

        self.assertEqual(response.status_code, 200)
        # Verify a new code was created (now there are 2)
        one_time_codes = OneTimeCode.objects.filter(
            combatant=self.combatant_with_privacy
        )
        self.assertEqual(one_time_codes.count(), 2)

        # The new code should be the one passed to send_info_update
        new_code = one_time_codes.exclude(id=existing_code.id).first()
        mock_send_info_update.assert_called_once_with(
            self.combatant_with_privacy, new_code
        )

    @patch("cards.views.home.send_privacy_policy")
    def test_update_info_post_existing_combatant_without_privacy(
        self, mock_send_privacy_policy
    ):
        """Test POST request for combatant who hasn't accepted privacy policy"""
        response = self.client.post(
            reverse("update-info"), {"update-info-email": "test2@example.com"}
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response, "If a combatant with this email exists, an email has been sent"
        )
        mock_send_privacy_policy.assert_called_once_with(self.combatant_without_privacy)

        # Verify no OneTimeCode was created
        self.assertFalse(
            OneTimeCode.objects.filter(
                combatant=self.combatant_without_privacy
            ).exists()
        )

    def test_update_info_post_nonexistent_combatant(self):
        """Test POST request for non-existent combatant"""
        response = self.client.post(
            reverse("update-info"), {"update-info-email": "nonexistent@example.com"}
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response, "If a combatant with this email exists, an email has been sent"
        )

    def test_update_info_post_no_email(self):
        """Test POST request with no email provided"""
        response = self.client.post(reverse("update-info"), {})

        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response, "If a combatant with this email exists, an email has been sent"
        )


class MarshalListViewTestCase(TestCase):
    """Test the marshal_list view"""

    def setUp(self):
        """Set up test data for marshal list tests"""
        from cards.models import (
            Authorization,
            Card,
            CombatantWarrant,
            Discipline,
            Marshal,
        )

        # Create test data
        self.discipline = Discipline.objects.create(
            name="Test Discipline", slug="test-discipline"
        )
        self.authorization = Authorization.objects.create(
            name="Test Auth", discipline=self.discipline, is_primary=True
        )
        self.marshal = Marshal.objects.create(
            name="Senior Marshal", discipline=self.discipline
        )

        self.combatant = Combatant.objects.create(
            sca_name="Test Marshal",
            legal_name="Test Legal Marshal",
            email="marshal@example.com",
            accepted_privacy_policy=True,
        )

        # Create a card and warrant
        self.card = Card.objects.create(
            combatant=self.combatant,
            discipline=self.discipline,
            date_issued="2024-01-01",
        )

        self.warrant = CombatantWarrant.objects.create(
            card=self.card, marshal=self.marshal
        )

    def test_marshal_list_get(self):
        """Test GET request to marshal_list view"""
        response = self.client.get(reverse("marshal-list"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Test Discipline")
        self.assertContains(response, "Test Marshal")

    def test_marshal_list_empty(self):
        """Test marshal list when no warrants exist"""
        # Delete the warrant
        self.warrant.delete()

        response = self.client.get(reverse("marshal-list"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Test Discipline")
        # Should still show discipline but no marshals
