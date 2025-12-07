"""Tests for DRF permission classes in cards.api.permissions."""

from types import SimpleNamespace
from unittest.mock import patch

from django.test import TestCase

from cards.api.permissions import (
    CardDatePermission,
    CombatantAuthorizationPermission,
    CombatantInfoPermission,
    CombatantMarshalPermission,
    ResendPrivacyPermission,
    WaiverDatePermission,
)
from sso_user.models import SSOUser


class BasePermissionTestCase(TestCase):
    """Base helpers for permission tests."""

    def setUp(self):
        self.user = SSOUser.objects.create_user(email="perm-test@example.com")

    def make_request(self, method: str, data=None):
        return SimpleNamespace(method=method.upper(), data=data or {}, user=self.user)


class CombatantInfoPermissionTests(BasePermissionTestCase):
    def setUp(self):
        super().setUp()
        self.permission = CombatantInfoPermission()

    @patch("cards.api.permissions.UserPermission.user_has_permission")
    def test_read_requires_read_combatant_info(self, mock_has_perm):
        request = self.make_request("GET")
        mock_has_perm.return_value = True

        self.assertTrue(self.permission.has_permission(request, view=object()))
        mock_has_perm.assert_called_with(self.user, "read_combatant_info")

        mock_has_perm.reset_mock()
        mock_has_perm.return_value = False
        self.assertFalse(self.permission.has_permission(request, view=object()))
        mock_has_perm.assert_called_with(self.user, "read_combatant_info")

    @patch("cards.api.permissions.UserPermission.user_has_permission")
    def test_write_requires_write_combatant_info(self, mock_has_perm):
        request = self.make_request("PATCH", data={"legal_name": "Updated"})
        mock_has_perm.return_value = True

        self.assertTrue(self.permission.has_permission(request, view=object()))
        mock_has_perm.assert_called_with(self.user, "write_combatant_info")

        mock_has_perm.reset_mock()
        mock_has_perm.return_value = False
        self.assertFalse(self.permission.has_permission(request, view=object()))
        mock_has_perm.assert_called_with(self.user, "write_combatant_info")


class WaiverDatePermissionTests(BasePermissionTestCase):
    def setUp(self):
        super().setUp()
        self.permission = WaiverDatePermission()

    @patch("cards.api.permissions.UserPermission.user_has_permission")
    def test_waiver_permission_required_for_read_and_write(self, mock_has_perm):
        mock_has_perm.return_value = True

        # GET
        request = self.make_request("GET")
        self.assertTrue(self.permission.has_permission(request, view=object()))
        mock_has_perm.assert_called_with(self.user, "write_waiver_date")

        mock_has_perm.reset_mock()

        # PUT
        request = self.make_request("PUT", data={"date_signed": "2024-01-01"})
        self.assertTrue(self.permission.has_permission(request, view=object()))
        mock_has_perm.assert_called_with(self.user, "write_waiver_date")

        # Denied when underlying permission check fails
        mock_has_perm.reset_mock()
        mock_has_perm.return_value = False
        request = self.make_request("GET")
        self.assertFalse(self.permission.has_permission(request, view=object()))
        mock_has_perm.assert_called_with(self.user, "write_waiver_date")


class CardDatePermissionTests(BasePermissionTestCase):
    def setUp(self):
        super().setUp()
        self.permission = CardDatePermission()

    @patch("cards.api.permissions.UserPermission.user_has_permission")
    def test_card_date_requires_permission_for_given_discipline(self, mock_has_perm):
        data = {
            "uuid": "00000000-0000-0000-0000-000000000000",
            "discipline_slug": "test",
            "date_issued": "2024-01-01",
        }
        request = self.make_request("PUT", data=data)
        mock_has_perm.return_value = True

        self.assertTrue(self.permission.has_permission(request, view=object()))
        mock_has_perm.assert_called_with(self.user, "write_card_date", "test")

        mock_has_perm.reset_mock()
        mock_has_perm.return_value = False
        self.assertFalse(self.permission.has_permission(request, view=object()))
        mock_has_perm.assert_called_with(self.user, "write_card_date", "test")

    @patch("cards.api.permissions.UserPermission.user_has_permission")
    def test_card_date_denied_when_discipline_missing(self, mock_has_perm):
        data = {
            "uuid": "00000000-0000-0000-0000-000000000000",
            # missing discipline_slug
            "date_issued": "2024-01-01",
        }
        request = self.make_request("PUT", data=data)
        self.assertFalse(self.permission.has_permission(request, view=object()))
        mock_has_perm.assert_not_called()


class AuthorizationMarshalPermissionTests(BasePermissionTestCase):
    def setUp(self):
        super().setUp()

    @patch("cards.api.permissions.UserPermission.user_has_permission")
    def test_combatant_authorization_permission_requires_discipline_permission(
        self, mock_has_perm
    ):
        permission = CombatantAuthorizationPermission()

        class DummyView:
            kwargs = {"discipline": "sword"}

        request = self.make_request("POST")
        mock_has_perm.return_value = True

        self.assertTrue(permission.has_permission(request, view=DummyView()))
        mock_has_perm.assert_called_with(
            self.user, "write_authorizations", "sword"
        )

        mock_has_perm.reset_mock()
        mock_has_perm.return_value = False
        self.assertFalse(permission.has_permission(request, view=DummyView()))
        mock_has_perm.assert_called_with(
            self.user, "write_authorizations", "sword"
        )

    @patch("cards.api.permissions.UserPermission.user_has_permission")
    def test_combatant_marshal_permission_requires_discipline_permission(
        self, mock_has_perm
    ):
        permission = CombatantMarshalPermission()

        class DummyView:
            kwargs = {"discipline": "sword"}

        request = self.make_request("POST")
        mock_has_perm.return_value = True

        self.assertTrue(permission.has_permission(request, view=DummyView()))
        mock_has_perm.assert_called_with(self.user, "write_marshal", "sword")

        mock_has_perm.reset_mock()
        mock_has_perm.return_value = False
        self.assertFalse(permission.has_permission(request, view=DummyView()))
        mock_has_perm.assert_called_with(self.user, "write_marshal", "sword")


class ResendPrivacyPermissionTests(BasePermissionTestCase):
    def setUp(self):
        super().setUp()
        self.permission = ResendPrivacyPermission()

    @patch("cards.api.permissions.UserPermission.user_has_permission")
    def test_resend_privacy_requires_read_combatant_info(self, mock_has_perm):
        request = self.make_request("POST", data={})
        mock_has_perm.return_value = True

        self.assertTrue(self.permission.has_permission(request, view=object()))
        mock_has_perm.assert_called_with(self.user, "read_combatant_info")

        mock_has_perm.reset_mock()
        mock_has_perm.return_value = False
        self.assertFalse(self.permission.has_permission(request, view=object()))
        mock_has_perm.assert_called_with(self.user, "read_combatant_info")


