"""Tests for the cards API endpoints."""

from datetime import timedelta

from cards.models import (Authorization, Card, Combatant,
                          CombatantAuthorization, Discipline, Marshal, Region,
                          Waiver)
from cards.utility.time import today
from django.test import TestCase
from django.urls import reverse
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
