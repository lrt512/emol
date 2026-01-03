"""Tests for the cards API endpoints."""

import uuid
from datetime import timedelta
from unittest.mock import patch

from cards.models import (
    Authorization,
    Card,
    Combatant,
    CombatantAuthorization,
    Discipline,
    Marshal,
    OneTimeCode,
    Permission,
    Region,
    UserPermission,
    Waiver,
)
from cards.utility.time import today
from django.test import TestCase, override_settings
from django.urls import reverse
from feature_switches.models import (
    ACCESS_MODE_DISABLED,
    ACCESS_MODE_GLOBAL,
    FeatureSwitch,
)
from rest_framework import status
from rest_framework.test import APIClient
from sso_user.models import SSOUser


class CombatantListAPITestCase(TestCase):
    """Tests for the combatant list API."""

    def setUp(self):
        """Set up test fixtures."""
        self.client = APIClient()
        self.user = SSOUser.objects.create_superuser(email="admin@example.com")
        self.combatant = Combatant.objects.create(
            sca_name="Test Fighter",
            legal_name="Test Legal",
            email="test@example.com",
            accepted_privacy_policy=True,
        )

    def test_combatant_list_authenticated(self):
        """Authenticated admin can list combatants."""
        self.client.force_authenticate(user=self.user)
        response = self.client.get(reverse("combatant-list-list"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)


class CombatantAPITestCase(TestCase):
    """Tests for the combatant detail API."""

    def setUp(self):
        """Set up test fixtures."""
        self.client = APIClient()
        self.user = SSOUser.objects.create_superuser(email="admin@example.com")
        self.region, _ = Region.objects.get_or_create(
            code="ON", defaults={"name": "Ontario", "active": True}
        )
        self.combatant = Combatant.objects.create(
            sca_name="Test Fighter",
            legal_name="Test Legal",
            email="test@example.com",
            accepted_privacy_policy=True,
            province="ON",
        )

    def test_combatant_retrieve(self):
        """Can retrieve a combatant by UUID."""
        self.client.force_authenticate(user=self.user)
        response = self.client.get(
            reverse("combatant-detail", kwargs={"uuid": self.combatant.uuid})
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["sca_name"], "Test Fighter")

    def test_combatant_update(self):
        """Can update a combatant."""
        self.client.force_authenticate(user=self.user)
        response = self.client.patch(
            reverse("combatant-detail", kwargs={"uuid": self.combatant.uuid}),
            {"sca_name": "Updated Name"},
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.combatant.refresh_from_db()
        self.assertEqual(self.combatant.sca_name, "Updated Name")

    def test_combatant_update_invalid_province(self):
        """Update with invalid province code is rejected."""
        self.client.force_authenticate(user=self.user)
        response = self.client.patch(
            reverse("combatant-detail", kwargs={"uuid": self.combatant.uuid}),
            {"province": "XX"},
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class CardAPITestCase(TestCase):
    """Tests for the card API."""

    def setUp(self):
        """Set up test fixtures."""
        self.client = APIClient()
        self.user = SSOUser.objects.create_superuser(email="admin@example.com")
        self.discipline = Discipline.objects.create(
            name="Test Combat", slug="test-combat"
        )
        self.authorization = Authorization.objects.create(
            name="Test Auth", slug="test-auth", discipline=self.discipline
        )
        self.marshal = Marshal.objects.create(
            name="Marshal", slug="marshal", discipline=self.discipline
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
        CombatantAuthorization.objects.create(
            card=self.card, authorization=self.authorization
        )

    def test_card_retrieve_by_combatant_uuid(self):
        """Can retrieve cards for a combatant."""
        self.client.force_authenticate(user=self.user)
        response = self.client.get(
            reverse("combatant-cards-detail", kwargs={"uuid": self.combatant.uuid})
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["discipline"]["name"], "Test Combat")


class CardDateAPITestCase(TestCase):
    """Tests for the card date update API."""

    def setUp(self):
        """Set up test fixtures."""
        self.client = APIClient()
        self.user = SSOUser.objects.create_superuser(email="admin@example.com")
        self.discipline = Discipline.objects.create(
            name="Test Combat", slug="test-combat"
        )
        self.combatant = Combatant.objects.create(
            sca_name="Test Fighter",
            legal_name="Test Legal",
            email="test@example.com",
            accepted_privacy_policy=True,
        )

    def test_card_date_update_creates_card(self):
        """Card date update creates card if not exists."""
        self.client.force_authenticate(user=self.user)
        response = self.client.put(
            reverse("card-date-detail", kwargs={"pk": 1}),
            {
                "uuid": str(self.combatant.uuid),
                "discipline_slug": "test-combat",
                "date_issued": str(today()),
            },
        )
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertTrue(
            Card.objects.filter(
                combatant=self.combatant, discipline=self.discipline
            ).exists()
        )

    def test_card_date_update_updates_existing(self):
        """Card date update modifies existing card."""
        self.client.force_authenticate(user=self.user)
        card = Card.objects.create(
            combatant=self.combatant,
            discipline=self.discipline,
            date_issued=today() - timedelta(days=100),
        )
        new_date = today()

        response = self.client.put(
            reverse("card-date-detail", kwargs={"pk": 1}),
            {
                "uuid": str(self.combatant.uuid),
                "discipline_slug": "test-combat",
                "date_issued": str(new_date),
            },
        )
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        card.refresh_from_db()
        self.assertEqual(card.date_issued, new_date)


class WaiverAPITestCase(TestCase):
    """Tests for the waiver API."""

    def setUp(self):
        """Set up test fixtures."""
        self.client = APIClient()
        self.user = SSOUser.objects.create_superuser(email="admin@example.com")
        self.combatant = Combatant.objects.create(
            sca_name="Test Fighter",
            legal_name="Test Legal",
            email="test@example.com",
            accepted_privacy_policy=True,
        )

    def test_waiver_update_creates_if_not_exists(self):
        """Waiver update creates waiver if not exists."""
        self.client.force_authenticate(user=self.user)
        response = self.client.put(
            reverse("waiver-detail", kwargs={"uuid": str(self.combatant.uuid)}),
            {"date_signed": str(today())},
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(Waiver.objects.filter(combatant=self.combatant).exists())

    def test_waiver_update_modifies_existing(self):
        """Waiver update modifies existing waiver."""
        self.client.force_authenticate(user=self.user)
        waiver = Waiver.objects.create(
            combatant=self.combatant,
            date_signed=today() - timedelta(days=100),
        )
        new_date = today()

        response = self.client.put(
            reverse("waiver-detail", kwargs={"uuid": str(self.combatant.uuid)}),
            {"date_signed": str(new_date)},
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        waiver.refresh_from_db()
        self.assertEqual(waiver.date_signed, new_date)

    def test_waiver_retrieve(self):
        """Can retrieve a waiver by combatant UUID."""
        self.client.force_authenticate(user=self.user)
        Waiver.objects.create(combatant=self.combatant, date_signed=today())

        response = self.client.get(
            reverse("waiver-detail", kwargs={"uuid": str(self.combatant.uuid)})
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("date_signed", response.data)


class CombatantAuthorizationAPITestCase(TestCase):
    """Tests for the combatant authorization API."""

    def setUp(self):
        """Set up test fixtures."""
        self.client = APIClient()
        self.user = SSOUser.objects.create_superuser(email="admin@example.com")
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
        self.card = Card.objects.create(
            combatant=self.combatant,
            discipline=self.discipline,
            date_issued=today(),
        )

    def test_add_authorization(self):
        """Can add an authorization to a combatant."""
        self.client.force_authenticate(user=self.user)
        response = self.client.post(
            reverse(
                "combatant-authorization-list",
                kwargs={"discipline": "test-combat"},
            ),
            {
                "combatant_uuid": str(self.combatant.uuid),
                "discipline": "test-combat",
                "authorization": "test-auth",
            },
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(
            CombatantAuthorization.objects.filter(
                card=self.card, authorization=self.authorization
            ).exists()
        )

    def test_remove_authorization(self):
        """Can remove an authorization from a combatant."""
        self.client.force_authenticate(user=self.user)
        ca = CombatantAuthorization.objects.create(
            card=self.card, authorization=self.authorization
        )

        response = self.client.delete(
            reverse(
                "combatant-authorization-detail",
                kwargs={"discipline": "test-combat", "uuid": str(ca.uuid)},
            )
        )
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(CombatantAuthorization.objects.filter(pk=ca.pk).exists())


class InitiatePinResetAPITestCase(TestCase):
    """Tests for the PIN reset initiation API."""

    def setUp(self):
        """Set up test fixtures."""
        self.client = APIClient()
        self.user = SSOUser.objects.create_user(email="mol@example.com")
        self.admin = SSOUser.objects.create_superuser(email="admin@example.com")

        self.permission, _ = Permission.objects.get_or_create(
            slug="can_initiate_pin_reset",
            defaults={"name": "Can initiate PIN reset", "is_global": True},
        )

        self.combatant = Combatant.objects.create(
            sca_name="Test Fighter",
            legal_name="Test Legal",
            email="test@example.com",
            accepted_privacy_policy=True,
        )

        FeatureSwitch.objects.create(
            name="pin_authentication", access_mode=ACCESS_MODE_GLOBAL
        )

    def test_pin_reset_requires_authentication(self):
        """Anonymous users cannot initiate PIN reset."""
        response = self.client.post(
            reverse("initiate-pin-reset"),
            {"combatant_uuid": str(self.combatant.uuid)},
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    @override_settings(NO_ENFORCE_PERMISSIONS=False)
    def test_pin_reset_requires_permission(self):
        """Users without permission cannot initiate PIN reset."""
        self.client.force_authenticate(user=self.user)
        response = self.client.post(
            reverse("initiate-pin-reset"),
            {"combatant_uuid": str(self.combatant.uuid)},
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_pin_reset_requires_feature_enabled(self):
        """PIN reset fails when feature is disabled."""
        FeatureSwitch.objects.filter(name="pin_authentication").update(
            access_mode=ACCESS_MODE_DISABLED
        )

        UserPermission.objects.create(
            user=self.user, permission=self.permission, discipline=None
        )
        self.client.force_authenticate(user=self.user)
        response = self.client.post(
            reverse("initiate-pin-reset"),
            {"combatant_uuid": str(self.combatant.uuid)},
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("not enabled", response.data["message"])

    def test_pin_reset_requires_combatant_has_pin(self):
        """PIN reset fails when combatant has no PIN."""
        UserPermission.objects.create(
            user=self.user, permission=self.permission, discipline=None
        )
        self.client.force_authenticate(user=self.user)
        response = self.client.post(
            reverse("initiate-pin-reset"),
            {"combatant_uuid": str(self.combatant.uuid)},
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("does not have a PIN", response.data["message"])

    @patch("cards.api.pin.send_pin_reset")
    def test_pin_reset_success(self, mock_send):
        """Successful PIN reset creates code and sends email."""
        self.combatant.set_pin("1234")
        self.combatant.save()

        UserPermission.objects.create(
            user=self.user, permission=self.permission, discipline=None
        )
        self.client.force_authenticate(user=self.user)

        response = self.client.post(
            reverse("initiate-pin-reset"),
            {"combatant_uuid": str(self.combatant.uuid)},
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("email sent", response.data["message"])

        mock_send.assert_called_once()
        code = OneTimeCode.objects.filter(combatant=self.combatant).first()
        self.assertIsNotNone(code)
        self.assertIn("pin/reset", code.url_template)

        self.combatant.refresh_from_db()
        self.assertFalse(self.combatant.has_pin)

    def test_pin_reset_combatant_not_found(self):
        """PIN reset fails for nonexistent combatant."""
        UserPermission.objects.create(
            user=self.user, permission=self.permission, discipline=None
        )
        self.client.force_authenticate(user=self.user)

        response = self.client.post(
            reverse("initiate-pin-reset"),
            {"combatant_uuid": str(uuid.uuid4())},
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    @patch("cards.api.pin.send_pin_reset")
    def test_superuser_can_reset_pin(self, mock_send):
        """Superusers can initiate PIN reset without explicit permission."""
        self.combatant.set_pin("5678")
        self.combatant.save()

        self.client.force_authenticate(user=self.admin)

        response = self.client.post(
            reverse("initiate-pin-reset"),
            {"combatant_uuid": str(self.combatant.uuid)},
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        mock_send.assert_called_once()


class CombatantListHasPinTestCase(TestCase):
    """Tests for has_pin field in combatant list API."""

    def setUp(self):
        """Set up test fixtures."""
        self.client = APIClient()
        self.user = SSOUser.objects.create_superuser(email="admin@example.com")

        self.combatant_with_pin = Combatant.objects.create(
            sca_name="With PIN",
            legal_name="Legal One",
            email="pin@example.com",
            accepted_privacy_policy=True,
        )
        self.combatant_with_pin.set_pin("1234")
        self.combatant_with_pin.save()

        self.combatant_no_pin = Combatant.objects.create(
            sca_name="No PIN",
            legal_name="Legal Two",
            email="nopin@example.com",
            accepted_privacy_policy=True,
        )

    def test_combatant_list_includes_has_pin(self):
        """Combatant list includes has_pin field."""
        self.client.force_authenticate(user=self.user)
        response = self.client.get(reverse("combatant-list-list"))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        combatants_by_name = {c["sca_name"]: c for c in response.data}

        self.assertTrue(combatants_by_name["With PIN"]["has_pin"])
        self.assertFalse(combatants_by_name["No PIN"]["has_pin"])
