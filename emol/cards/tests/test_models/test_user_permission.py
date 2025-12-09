from cards.models.discipline import Discipline
from cards.models.permission import Permission
from cards.models.user_permission import UserPermission
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from django.core.exceptions import ValidationError
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

    def test_model_validation_global_permission_with_discipline_fails(self):
        """Model validation should prevent global permissions from having disciplines"""
        with self.assertRaises(ValidationError) as context:
            UserPermission.objects.create(
                user=self.user,
                permission=self.global_permission,
                discipline=self.discipline,
            )

        self.assertIn("discipline", context.exception.message_dict)
        self.assertIn(
            "Global permission", context.exception.message_dict["discipline"][0]
        )

    def test_model_validation_non_global_permission_without_discipline_fails(self):
        """Model validation should prevent non-global permissions from being assigned without disciplines"""
        with self.assertRaises(ValidationError) as context:
            UserPermission.objects.create(
                user=self.user,
                permission=self.permission,  # non-global permission
                discipline=None,
            )

        self.assertIn("discipline", context.exception.message_dict)
        self.assertIn(
            "requires a discipline", context.exception.message_dict["discipline"][0]
        )

    def test_model_validation_global_permission_without_discipline_succeeds(self):
        """Global permissions should be allowed without disciplines"""
        user_perm = UserPermission.objects.create(
            user=self.user, permission=self.global_permission, discipline=None
        )

        self.assertIsNotNone(user_perm.id)
        self.assertEqual(user_perm.discipline, None)

    def test_model_validation_non_global_permission_with_discipline_succeeds(self):
        """Non-global permissions should be allowed with disciplines"""
        user_perm = UserPermission.objects.create(
            user=self.user, permission=self.permission, discipline=self.discipline
        )

        self.assertIsNotNone(user_perm.id)
        self.assertEqual(user_perm.discipline, self.discipline)

    @override_settings(NO_ENFORCE_PERMISSIONS=False)
    def test_global_permission_ignores_discipline_parameter(self):
        """When checking global permissions, the discipline parameter should be ignored"""
        # Create a global permission assignment (correctly with discipline=None)
        UserPermission.objects.create(
            user=self.user, permission=self.global_permission, discipline=None
        )

        # Global permission should be granted regardless of what discipline is requested
        self.assertTrue(
            UserPermission.user_has_permission(
                self.user, self.global_permission.name, None
            )
        )
        self.assertTrue(
            UserPermission.user_has_permission(
                self.user, self.global_permission.name, self.discipline.name
            )
        )
        self.assertTrue(
            UserPermission.user_has_permission(
                self.user, self.global_permission.name, "any_discipline"
            )
        )

    @override_settings(NO_ENFORCE_PERMISSIONS=False)
    def test_non_global_permission_requires_specific_discipline(self):
        """Non-global permissions should only be granted for the specific assigned discipline"""
        other_discipline = Discipline.objects.create(name="Other Discipline")

        # Assign permission to specific discipline
        UserPermission.objects.create(
            user=self.user, permission=self.permission, discipline=self.discipline
        )

        # Should have permission for the assigned discipline
        self.assertTrue(
            UserPermission.user_has_permission(
                self.user, self.permission.name, self.discipline.name
            )
        )

        # Should NOT have permission for other disciplines
        self.assertFalse(
            UserPermission.user_has_permission(
                self.user, self.permission.name, other_discipline.name
            )
        )

        # Should NOT have permission when no discipline specified
        self.assertFalse(
            UserPermission.user_has_permission(self.user, self.permission.name, None)
        )
