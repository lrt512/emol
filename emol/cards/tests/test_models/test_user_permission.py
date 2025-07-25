from cards.models.discipline import Discipline
from cards.models.permission import Permission
from cards.models.user_permission import UserPermission
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from django.test import TestCase
from django.test.utils import override_settings

User = get_user_model()


class UserPermissionTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(email="test@example.com")
        self.global_permission = Permission.objects.create(
            name="Test Global Permission", is_global=True
        )
        self.permission = Permission.objects.create(
            name="Test Permission", is_global=False
        )
        self.discipline = Discipline.objects.create(name="Test Discipline")

    def test_user_has_permission_global(self):
        UserPermission.objects.create(
            user=self.user, permission=self.global_permission, discipline=None
        )
        self.assertTrue(
            UserPermission.user_has_permission(self.user, self.global_permission.name)
        )

    def test_user_has_permission_non_global(self):
        UserPermission.objects.create(
            user=self.user, permission=self.permission, discipline=self.discipline
        )
        self.assertTrue(
            UserPermission.user_has_permission(
                self.user, self.permission.name, self.discipline.name
            )
        )

    @override_settings(NO_ENFORCE_PERMISSIONS=False)
    def test_user_has_permission_invalid_permission(self):
        self.assertFalse(
            UserPermission.user_has_permission(self.user, "invalid_permission")
        )

    @override_settings(NO_ENFORCE_PERMISSIONS=False)
    def test_user_has_permission_invalid_discipline(self):
        self.assertFalse(
            UserPermission.user_has_permission(
                self.user, self.permission.name, "invalid_discipline"
            )
        )

    def test_user_has_permission_no_user(self):
        self.assertFalse(
            UserPermission.user_has_permission(None, "test_global_permission")
        )

    def test_user_has_permission_anonymous_user(self):
        anonymous_user = AnonymousUser()
        self.assertFalse(
            UserPermission.user_has_permission(
                anonymous_user, self.global_permission.name
            )
        )

    def test_user_has_permission_no_enforce_permissions(self):
        with self.settings(NO_ENFORCE_PERMISSIONS=True):
            self.assertTrue(
                UserPermission.user_has_permission(
                    self.user, self.global_permission.name
                )
            )

    @override_settings(NO_ENFORCE_PERMISSIONS=False)
    def test_user_has_permission_no_permission(self):
        self.assertFalse(
            UserPermission.user_has_permission(self.user, self.global_permission.name)
        )

    @override_settings(NO_ENFORCE_PERMISSIONS=False)
    def test_user_has_permission_no_permission_non_global(self):
        self.assertFalse(
            UserPermission.user_has_permission(
                self.user, self.permission.name, self.discipline.name
            )
        )
