from datetime import timedelta
from unittest.mock import patch
from uuid import uuid4

from cards.models import Combatant, OneTimeCode, Region
from cards.views.self_serve_update import (
    SelfServeUpdateSerializer,
    serializer_errors_to_strings,
)
from django.test import RequestFactory, TestCase
from django.urls import reverse
from django.utils import timezone


class SelfServeUpdateSerializerTestCase(TestCase):
    """Test the SelfServeUpdateSerializer"""

    def setUp(self):
        """Set up test data"""
        self.combatant = Combatant.objects.create(
            sca_name="Test Fighter",
            legal_name="Test Legal",
            email="test@example.com",
            phone="555-1234",
            address1="123 Main St",
            city="Test City",
            province="ON",
            postal_code="K1A 0A6",
            accepted_privacy_policy=True,
        )

    def test_valid_data_serialization(self):
        """Test serialization with valid data"""
        data = {
            "sca_name": "Updated Fighter",
            "legal_name": "Updated Legal",
            "phone": "555-5678",
            "address1": "456 Oak Ave",
            "address2": "Apt 2",
            "city": "New City",
            "province": "ON",
            "postal_code": "V6B 2W2",
            "member_number": "123456",
            "member_expiry": "2025-12-31",
        }

        serializer = SelfServeUpdateSerializer(instance=self.combatant, data=data)
        self.assertTrue(serializer.is_valid())

        updated_combatant = serializer.save()
        self.assertEqual(updated_combatant.sca_name, "Updated Fighter")
        self.assertEqual(updated_combatant.legal_name, "Updated Legal")
        self.assertEqual(updated_combatant.phone, "555-5678")
        self.assertEqual(updated_combatant.member_number, 123456)

    def test_required_fields_validation(self):
        """Test that required fields are validated"""
        data = {
            "sca_name": "Test",
            # Missing required fields
        }

        serializer = SelfServeUpdateSerializer(instance=self.combatant, data=data)
        self.assertFalse(serializer.is_valid())

        required_fields = [
            "legal_name",
            "phone",
            "address1",
            "city",
            "province",
            "postal_code",
        ]
        for field in required_fields:
            self.assertIn(field, serializer.errors)

    def test_optional_fields(self):
        """Test that optional fields can be omitted"""
        data = {
            "legal_name": "Updated Legal",
            "phone": "555-5678",
            "address1": "456 Oak Ave",
            "city": "New City",
            "province": "ON",
            "postal_code": "V6B 2W2",
            # Optional fields omitted: sca_name, address2, member_number, member_expiry
        }

        serializer = SelfServeUpdateSerializer(instance=self.combatant, data=data)
        self.assertTrue(serializer.is_valid())

    def test_member_expiry_requires_member_number(self):
        """Test that member_expiry requires member_number"""
        data = {
            "legal_name": "Test Legal",
            "phone": "555-1234",
            "address1": "123 Main St",
            "city": "Test City",
            "province": "ON",
            "postal_code": "K1A 0A6",
            "member_expiry": "2025-12-31",
            # member_number is missing
        }

        serializer = SelfServeUpdateSerializer(instance=self.combatant, data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("member_number", serializer.errors)
        self.assertEqual(
            str(serializer.errors["member_number"][0]),
            "Member number is required when specifying an expiry date.",
        )

    def test_member_number_without_expiry_allowed(self):
        """Test that member_number can be specified without member_expiry"""
        data = {
            "legal_name": "Test Legal",
            "phone": "555-1234",
            "address1": "123 Main St",
            "city": "Test City",
            "province": "ON",
            "postal_code": "K1A 0A6",
            "member_number": "123456",
            # member_expiry is omitted
        }

        serializer = SelfServeUpdateSerializer(instance=self.combatant, data=data)
        self.assertTrue(serializer.is_valid())

    def test_blank_string_cleaning(self):
        """Test that blank strings are converted to None for clean_fields"""
        data = {
            "legal_name": "Test Legal",
            "phone": "555-1234",
            "address1": "123 Main St",
            "city": "Test City",
            "province": "ON",
            "postal_code": "K1A 0A6",
            "sca_name": "",  # Should be cleaned to None
            "address2": "",  # Should be cleaned to None
            "member_number": "",  # Should be cleaned to None
            "member_expiry": "",  # Should be cleaned to None
        }

        serializer = SelfServeUpdateSerializer(instance=self.combatant, data=data)
        self.assertTrue(serializer.is_valid())

        updated_combatant = serializer.save()
        self.assertIsNone(updated_combatant.sca_name)
        self.assertIsNone(updated_combatant.address2)
        self.assertIsNone(updated_combatant.member_number)
        self.assertIsNone(updated_combatant.member_expiry)

    def test_partial_update(self):
        """Test partial updates work correctly"""
        data = {
            "sca_name": "Partially Updated",
            "phone": "555-9999",
        }

        serializer = SelfServeUpdateSerializer(
            instance=self.combatant, data=data, partial=True
        )
        self.assertTrue(serializer.is_valid())

        updated_combatant = serializer.save()
        self.assertEqual(updated_combatant.sca_name, "Partially Updated")
        self.assertEqual(updated_combatant.phone, "555-9999")
        # Other fields should remain unchanged
        self.assertEqual(updated_combatant.legal_name, "Test Legal")
        self.assertEqual(updated_combatant.address1, "123 Main St")

    def test_invalid_province_validation(self):
        """Test that invalid province codes are rejected"""
        data = {
            "legal_name": "Test Legal",
            "phone": "555-1234",
            "address1": "123 Main St",
            "city": "Test City",
            "province": "XX",  # Invalid province code
            "postal_code": "K1A 0A6",
        }

        serializer = SelfServeUpdateSerializer(instance=self.combatant, data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("province", serializer.errors)

    def test_valid_province_validation(self):
        """Test that valid province codes are accepted"""
        data = {
            "legal_name": "Test Legal",
            "phone": "555-1234",
            "address1": "123 Main St",
            "city": "Test City",
            "province": "ON",  # Valid province code
            "postal_code": "K1A 0A6",
        }

        serializer = SelfServeUpdateSerializer(instance=self.combatant, data=data)
        self.assertTrue(serializer.is_valid())


class SerializerErrorsToStringsTestCase(TestCase):
    """Test the serializer_errors_to_strings utility function"""

    def test_single_field_single_error(self):
        """Test conversion of single field with single error"""
        errors = {"legal_name": ["This field is required."]}
        result = serializer_errors_to_strings(
            type("MockSerializer", (), {"errors": errors})()
        )
        self.assertEqual(result, ["legal_name: This field is required."])

    def test_multiple_fields_multiple_errors(self):
        """Test conversion of multiple fields with multiple errors"""
        errors = {
            "legal_name": ["This field is required."],
            "phone": ["This field is required.", "Invalid format."],
        }
        mock_serializer = type("MockSerializer", (), {"errors": errors})()
        result = serializer_errors_to_strings(mock_serializer)

        expected = [
            "legal_name: This field is required.",
            "phone: This field is required.",
            "phone: Invalid format.",
        ]
        self.assertEqual(result, expected)

    def test_empty_errors(self):
        """Test handling of empty errors"""
        errors = {}
        mock_serializer = type("MockSerializer", (), {"errors": errors})()
        result = serializer_errors_to_strings(mock_serializer)
        self.assertEqual(result, [])


class SelfServeUpdateViewTestCase(TestCase):
    """Test the self_serve_update view"""

    def setUp(self):
        """Set up test data"""
        self.combatant = Combatant.objects.create(
            sca_name="Test Fighter",
            legal_name="Test Legal",
            email="test@example.com",
            phone="555-1234",
            address1="123 Main St",
            city="Test City",
            province="ON",
            postal_code="K1A 0A6",
            accepted_privacy_policy=True,
        )

        self.region, _ = Region.objects.get_or_create(
            code="ON",
            defaults={
                "name": "Ontario",
                "country": "Canada",
                "postal_format": "A1A 1A1",
                "active": True,
            },
        )

        self.update_code = OneTimeCode.objects.create(
            combatant=self.combatant,
            url_template="/self-serve-update/{code}",
            expires_at=timezone.now() + timedelta(hours=24),
        )

        self.factory = RequestFactory()

    def test_get_valid_code(self):
        """Test GET request with valid update code"""
        response = self.client.get(
            reverse("self-serve-update", args=[str(self.update_code.code)])
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Test Fighter")
        self.assertContains(response, "Test Legal")
        self.assertContains(response, "test@example.com")
        self.assertContains(response, self.update_code.code)

    def test_get_invalid_code(self):
        """Test GET request with invalid update code"""
        invalid_code = uuid4()
        response = self.client.get(
            reverse("self-serve-update", args=[str(invalid_code)])
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response, "The update code provided is invalid or has already been used."
        )

    def test_get_nonexistent_code(self):
        """Test GET request with non-existent update code"""
        response = self.client.get(
            reverse("self-serve-update", args=["nonexistent-code"])
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response, "The update code provided is invalid or has already been used."
        )

    def test_post_valid_data(self):
        """Test POST request with valid data"""
        data = {
            "sca_name": "Updated Fighter",
            "legal_name": "Updated Legal",
            "phone": "555-5678",
            "address1": "456 Oak Ave",
            "address2": "Apt 2",
            "city": "New City",
            "province": "ON",
            "postal_code": "V6B 2W2",
            "member_number": "123456",
            "member_expiry": "2025-12-31",
        }

        response = self.client.post(
            reverse("self-serve-update", args=[str(self.update_code.code)]), data=data
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Your information has been updated successfully.")

        # Verify the combatant was updated
        self.combatant.refresh_from_db()
        self.assertEqual(self.combatant.sca_name, "Updated Fighter")
        self.assertEqual(self.combatant.legal_name, "Updated Legal")
        self.assertEqual(self.combatant.phone, "555-5678")

        # Verify the update code was consumed
        self.update_code.refresh_from_db()
        self.assertTrue(self.update_code.consumed)

    def test_post_invalid_data(self):
        """Test POST request with invalid data (member_expiry without member_number)"""
        data = {
            "legal_name": "Updated Legal",
            "phone": "555-5678",
            "address1": "456 Oak Ave",
            "city": "New City",
            "province": "ON",
            "postal_code": "V6B 2W2",
            "member_expiry": "2025-12-31",
            # member_number is missing - this should cause validation error
        }

        response = self.client.post(
            reverse("self-serve-update", args=[str(self.update_code.code)]), data=data
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "There was an error updating your information.")

        # Verify the combatant was not updated
        self.combatant.refresh_from_db()
        self.assertEqual(self.combatant.sca_name, "Test Fighter")

        # Verify the update code is still valid (not consumed)
        self.update_code.refresh_from_db()
        self.assertFalse(self.update_code.consumed)

    def test_post_member_expiry_without_number(self):
        """Test POST request with member_expiry but no member_number"""
        data = {
            "legal_name": "Updated Legal",
            "phone": "555-5678",
            "address1": "456 Oak Ave",
            "city": "New City",
            "province": "ON",
            "postal_code": "V6B 2W2",
            "member_expiry": "2025-12-31",
            # member_number is missing
        }

        response = self.client.post(
            reverse("self-serve-update", args=[str(self.update_code.code)]), data=data
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "There was an error updating your information.")
        self.assertContains(response, "member_number")

    def test_post_blank_string_cleaning(self):
        """Test POST request with blank strings that should be cleaned"""
        data = {
            "sca_name": "",  # Should be cleaned to None
            "legal_name": "Updated Legal",
            "phone": "555-5678",
            "address1": "456 Oak Ave",
            "address2": "",  # Should be cleaned to None
            "city": "New City",
            "province": "ON",
            "postal_code": "V6B 2W2",
            "member_number": "",  # Should be cleaned to None
            "member_expiry": "",  # Should be cleaned to None
        }

        response = self.client.post(
            reverse("self-serve-update", args=[str(self.update_code.code)]), data=data
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Your information has been updated successfully.")

        # Verify blank strings were cleaned to None
        self.combatant.refresh_from_db()
        self.assertIsNone(self.combatant.sca_name)
        self.assertIsNone(self.combatant.address2)
        self.assertIsNone(self.combatant.member_number)
        self.assertIsNone(self.combatant.member_expiry)

    def test_post_partial_update(self):
        """Test POST request with partial data update"""
        data = {
            "legal_name": "Updated Legal",
            "phone": "555-9999",
            "address1": "456 Oak Ave",
            "city": "New City",
            "province": "ON",
            "postal_code": "V6B 2W2",
            # Other fields omitted
        }

        response = self.client.post(
            reverse("self-serve-update", args=[str(self.update_code.code)]), data=data
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Your information has been updated successfully.")

        # Verify only specified fields were updated
        self.combatant.refresh_from_db()
        self.assertEqual(self.combatant.legal_name, "Updated Legal")
        self.assertEqual(self.combatant.phone, "555-9999")
        self.assertEqual(
            self.combatant.sca_name, "Test Fighter"
        )  # Should remain unchanged

    def test_post_invalid_code(self):
        """Test POST request with invalid update code"""
        invalid_code = uuid4()
        data = {
            "legal_name": "Updated Legal",
            "phone": "555-5678",
            "address1": "456 Oak Ave",
            "city": "New City",
            "province": "ON",
            "postal_code": "V6B 2W2",
        }

        response = self.client.post(
            reverse("self-serve-update", args=[str(invalid_code)]), data=data
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response, "The update code provided is invalid or has already been used."
        )

    @patch("cards.views.self_serve_update.logger")
    def test_exception_handling(self, mock_logger):
        """Test handling of unexpected exceptions"""
        with patch("cards.views.self_serve_update.OneTimeCode.objects.get") as mock_get:
            mock_get.side_effect = Exception("Database error")

            response = self.client.get(
                reverse("self-serve-update", args=[str(self.update_code.code)])
            )

            self.assertEqual(response.status_code, 200)
            self.assertContains(
                response, "An unexpected error occurred. Please try again later."
            )
            mock_logger.exception.assert_called_once()

    def test_context_data_on_get(self):
        """Test that GET request includes proper context data"""
        response = self.client.get(
            reverse("self-serve-update", args=[str(self.update_code.code)])
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["self_serve"], True)
        self.assertEqual(response.context["code"], str(self.update_code.code))
        self.assertEqual(response.context["combatant"], self.combatant)
        self.assertIn("regions", response.context)

    def test_context_data_on_post_error(self):
        """Test that POST request with errors includes proper context data"""
        data = {
            "legal_name": "Test Legal",
            "phone": "555-1234",
            "address1": "123 Main St",
            "city": "Test City",
            "province": "ON",
            "postal_code": "K1A 0A6",
            "member_expiry": "2025-12-31",
            # member_number is missing - this will trigger validation error
        }

        response = self.client.post(
            reverse("self-serve-update", args=[str(self.update_code.code)]), data=data
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["self_serve"], True)
        self.assertEqual(response.context["code"], str(self.update_code.code))
        self.assertEqual(response.context["combatant"], self.combatant)
        self.assertIn("regions", response.context)
        self.assertIn("message", response.context)
        self.assertIn("errors", response.context)

    def test_update_code_consumed_after_successful_update(self):
        """Test that update code is consumed after successful update"""
        data = {
            "legal_name": "Updated Legal",
            "phone": "555-5678",
            "address1": "456 Oak Ave",
            "city": "New City",
            "province": "ON",
            "postal_code": "V6B 2W2",
        }

        response = self.client.post(
            reverse("self-serve-update", args=[str(self.update_code.code)]), data=data
        )

        self.assertEqual(response.status_code, 200)
        self.update_code.refresh_from_db()
        self.assertTrue(self.update_code.consumed)

    def test_update_code_preserved_after_failed_update(self):
        """Test that update code is not consumed after failed update"""
        data = {
            "legal_name": "Test Legal",
            "phone": "555-1234",
            "address1": "123 Main St",
            "city": "Test City",
            "province": "ON",
            "postal_code": "K1A 0A6",
            "member_expiry": "2025-12-31",
        }

        response = self.client.post(
            reverse("self-serve-update", args=[str(self.update_code.code)]), data=data
        )

        self.assertEqual(response.status_code, 200)
        self.update_code.refresh_from_db()
        self.assertFalse(self.update_code.consumed)


class OneTimeCodeModelTestCase(TestCase):
    """Test the OneTimeCode model functionality"""

    def setUp(self):
        """Set up test data"""
        self.combatant = Combatant.objects.create(
            sca_name="Test Fighter",
            legal_name="Test Legal",
            email="test@example.com",
            phone="555-1234",
            address1="123 Main St",
            city="Test City",
            province="ON",
            postal_code="K1A 0A6",
            accepted_privacy_policy=True,
        )

    def test_one_time_code_creation(self):
        """Test creating a one-time code"""
        one_time_code = OneTimeCode.objects.create(
            combatant=self.combatant,
            url_template="/test/{code}",
        )

        self.assertIsNotNone(one_time_code.code)
        self.assertEqual(one_time_code.combatant, self.combatant)
        self.assertIsNotNone(one_time_code.expires_at)
        self.assertFalse(one_time_code.consumed)

    def test_one_time_code_str_representation(self):
        """Test string representation of one-time code"""
        one_time_code = OneTimeCode.objects.create(
            combatant=self.combatant,
            url_template="/test/{code}",
        )
        str_repr = str(one_time_code)

        self.assertIn("test@example.com", str_repr)
        self.assertIn("OneTimeCode:", str_repr)
        self.assertIn("[ACTIVE]", str_repr)

    def test_one_time_code_url_property(self):
        """Test URL property generation"""
        one_time_code = OneTimeCode.objects.create(
            combatant=self.combatant,
            url_template="/self-serve-update/{code}",
        )
        url = one_time_code.url

        self.assertIn(str(one_time_code.code), url)
        self.assertIn("self-serve-update", url)

    def test_one_time_code_consume(self):
        """Test consuming a one-time code"""
        one_time_code = OneTimeCode.objects.create(
            combatant=self.combatant,
            url_template="/test/{code}",
        )

        self.assertTrue(one_time_code.is_valid)
        result = one_time_code.consume()
        self.assertTrue(result)
        self.assertTrue(one_time_code.consumed)
        self.assertIsNotNone(one_time_code.consumed_at)
        self.assertFalse(one_time_code.is_valid)

        # Second consume should fail
        result = one_time_code.consume()
        self.assertFalse(result)

    def test_one_time_code_str_expired(self):
        """Test string representation shows EXPIRED status"""
        one_time_code = OneTimeCode.objects.create(
            combatant=self.combatant,
            url_template="/test/{code}",
            expires_at=timezone.now() - timedelta(hours=1),
        )
        str_repr = str(one_time_code)

        self.assertIn("[EXPIRED]", str_repr)

    def test_one_time_code_str_used(self):
        """Test string representation shows USED status"""
        one_time_code = OneTimeCode.objects.create(
            combatant=self.combatant,
            url_template="/test/{code}",
        )
        one_time_code.consume()
        str_repr = str(one_time_code)

        self.assertIn("[USED]", str_repr)
