"""Tests for privacy-related views."""

import uuid
from datetime import datetime

from cards.models import Combatant, Permission, PrivacyPolicy, UserPermission
from django.test import TestCase, override_settings
from django.urls import reverse
from feature_switches.models import ACCESS_MODE_GLOBAL, ACCESS_MODE_LIST, FeatureSwitch
from sso_user.models import SSOUser


class PrivacyPolicyViewTestCase(TestCase):
    """Tests for the privacy policy view."""

    def setUp(self):
        """Set up test fixtures."""
        year = datetime.now().year
        PrivacyPolicy.objects.create(
            text="# Test Privacy Policy\n\nThis is a test.",
            version=f"{year}.1",
            approved=True,
            changelog="Initial test policy",
        )
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
        response = self.client.get(reverse("privacy-policy", kwargs={"code": code}))
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
        self.assertTemplateUsed(response, "home/registration_completed.html")
        self.combatant.refresh_from_db()
        self.assertTrue(self.combatant.accepted_privacy_policy)

    @override_settings(SEND_EMAIL=False, SITE_URL="http://test.example.com")
    def test_privacy_policy_accept_with_pin_enabled(self):
        """POST with accept redirects to PIN setup when PIN is enabled."""
        FeatureSwitch.objects.create(
            name="pin_authentication", access_mode=ACCESS_MODE_GLOBAL
        )

        code = self.combatant.privacy_acceptance_code
        response = self.client.post(
            reverse("privacy-policy", kwargs={"code": code}),
            {"code": code, "accept": "1"},
        )
        self.assertEqual(response.status_code, 302)
        self.assertIn("/pin/setup/", response.url)
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

    @override_settings(SEND_EMAIL=False, SITE_URL="http://test.example.com")
    def test_privacy_policy_accept_with_pin_list_mode_combatant_in_list(self):
        """POST with accept redirects to PIN setup when combatant is in list."""
        switch = FeatureSwitch.objects.create(
            name="pin_authentication", access_mode=ACCESS_MODE_LIST
        )
        switch.allowed_users.add(self.combatant)

        code = self.combatant.privacy_acceptance_code
        response = self.client.post(
            reverse("privacy-policy", kwargs={"code": code}),
            {"code": code, "accept": "1"},
        )
        self.assertEqual(response.status_code, 302)
        self.assertIn("/pin/setup/", response.url)
        self.combatant.refresh_from_db()
        self.assertTrue(self.combatant.accepted_privacy_policy)

    @override_settings(SEND_EMAIL=False, SITE_URL="http://test.example.com")
    def test_privacy_policy_accept_with_pin_list_mode_combatant_not_in_list(self):
        """POST with accept shows accepted page when combatant not in list."""
        FeatureSwitch.objects.create(
            name="pin_authentication", access_mode=ACCESS_MODE_LIST
        )

        code = self.combatant.privacy_acceptance_code
        response = self.client.post(
            reverse("privacy-policy", kwargs={"code": code}),
            {"code": code, "accept": "1"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "home/registration_completed.html")
        self.combatant.refresh_from_db()
        self.assertTrue(self.combatant.accepted_privacy_policy)


class PrivacyPolicyDraftWorkflowTestCase(TestCase):
    """Tests for the privacy policy draft workflow."""

    def setUp(self):
        """Set up test fixtures."""
        year = datetime.now().year
        self.user = SSOUser.objects.create_user(email="editor@example.com")
        self.permission, _ = Permission.objects.get_or_create(
            slug="can_edit_privacy_policy",
            defaults={"name": "Can edit privacy policy", "is_global": True},
        )
        UserPermission.objects.create(
            user=self.user, permission=self.permission, discipline=None
        )
        self.approved_policy = PrivacyPolicy.objects.create(
            text="# Approved Policy\n\nThis is approved.",
            version=f"{year}.1",
            approved=True,
            changelog="Initial approved policy",
        )

    @override_settings(NO_ENFORCE_PERMISSIONS=False)
    def test_edit_privacy_policy_requires_permission(self):
        """Edit view requires can_edit_privacy_policy permission."""
        response = self.client.get(reverse("edit-privacy-policy"))
        self.assertEqual(response.status_code, 401)

    def test_edit_privacy_policy_get_no_draft(self):
        """GET edit view with no draft shows landing page."""
        self.client.force_login(self.user)
        response = self.client.get(reverse("edit-privacy-policy"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Edit Privacy Policy")
        self.assertContains(response, "Create Draft")
        self.assertNotContains(response, "Save Draft")

    def test_create_draft_from_latest(self):
        """Create draft button creates draft from latest approved policy."""
        self.client.force_login(self.user)
        response = self.client.post(
            reverse("edit-privacy-policy"), {"create_draft": "1"}
        )
        self.assertEqual(response.status_code, 302)
        draft = PrivacyPolicy.objects.filter(approved=False).first()
        self.assertIsNotNone(draft)
        self.assertEqual(draft.text, self.approved_policy.text)
        self.assertIsNotNone(draft.draft_uuid)
        self.assertFalse(draft.approved)

    def test_create_draft_when_draft_exists(self):
        """Create draft when one exists redirects to edit."""
        self.client.force_login(self.user)
        PrivacyPolicy.objects.create(
            text="Existing draft", approved=False, changelog=""
        )
        response = self.client.post(
            reverse("edit-privacy-policy"), {"create_draft": "1"}
        )
        self.assertEqual(response.status_code, 302)

    def test_edit_draft_save(self):
        """Saving a draft updates it."""
        self.client.force_login(self.user)
        draft = PrivacyPolicy.objects.create(
            text="Original text", approved=False, changelog="Original changelog"
        )
        response = self.client.post(
            reverse("edit-privacy-policy"),
            {
                "text": "Updated text",
                "changelog": "Updated changelog",
            },
        )
        self.assertEqual(response.status_code, 200)
        draft.refresh_from_db()
        self.assertEqual(draft.text, "Updated text")
        self.assertEqual(draft.changelog, "Updated changelog")

    def test_edit_draft_requires_text(self):
        """Saving draft without text shows error."""
        self.client.force_login(self.user)
        draft = PrivacyPolicy.objects.create(
            text="Original text", approved=False, changelog=""
        )
        response = self.client.post(
            reverse("edit-privacy-policy"),
            {
                "text": "",
                "changelog": "Changelog",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Policy text is required")
        draft.refresh_from_db()
        self.assertEqual(draft.text, "Original text")

    def test_delete_draft(self):
        """Delete draft removes the draft."""
        self.client.force_login(self.user)
        draft = PrivacyPolicy.objects.create(
            text="Draft text", approved=False, changelog=""
        )
        draft_uuid = draft.draft_uuid
        response = self.client.post(
            reverse("edit-privacy-policy"), {"delete_draft": "1"}
        )
        self.assertEqual(response.status_code, 302)
        self.assertFalse(PrivacyPolicy.objects.filter(draft_uuid=draft_uuid).exists())

    def test_view_draft_public(self):
        """View draft is publicly accessible."""
        draft = PrivacyPolicy.objects.create(
            text="# Draft Policy\n\nThis is a draft.",
            approved=False,
            changelog="Test changelog",
        )
        response = self.client.get(
            reverse("view-draft", kwargs={"draft_uuid": draft.draft_uuid})
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Draft Policy")
        self.assertContains(response, "Test changelog")
        self.assertContains(response, "draft version")

    def test_view_draft_approved_redirects(self):
        """Viewing approved draft redirects to version view."""
        year = datetime.now().year
        draft = PrivacyPolicy.objects.create(
            text="# Draft Policy",
            approved=False,
            changelog="Test changelog",
        )
        draft_uuid = draft.draft_uuid
        draft.approve()
        draft.refresh_from_db()
        response = self.client.get(
            reverse("view-draft", kwargs={"draft_uuid": draft_uuid})
        )
        self.assertEqual(response.status_code, 302)
        self.assertIn(f"/privacy-policy/version/{draft.version}", response.url)

    def test_view_draft_not_found(self):
        """Viewing non-existent draft returns 404."""
        fake_uuid = uuid.uuid4()
        response = self.client.get(
            reverse("view-draft", kwargs={"draft_uuid": fake_uuid})
        )
        self.assertEqual(response.status_code, 404)

    @override_settings(NO_ENFORCE_PERMISSIONS=False)
    def test_approve_policy_requires_permission(self):
        """Approve view requires can_edit_privacy_policy permission."""
        draft = PrivacyPolicy.objects.create(
            text="Draft text", approved=False, changelog="Test changelog"
        )
        response = self.client.post(
            reverse("approve-policy", kwargs={"draft_uuid": draft.draft_uuid})
        )
        self.assertEqual(response.status_code, 401)

    def test_approve_policy(self):
        """Approving a draft generates version and marks as approved."""
        self.client.force_login(self.user)
        year = datetime.now().year
        draft = PrivacyPolicy.objects.create(
            text="Draft text", approved=False, changelog="Test changelog"
        )
        response = self.client.post(
            reverse("approve-policy", kwargs={"draft_uuid": draft.draft_uuid})
        )
        self.assertEqual(response.status_code, 302)
        draft.refresh_from_db()
        self.assertTrue(draft.approved)
        self.assertEqual(draft.version, f"{year}.2")
        self.assertIn(f"/privacy-policy/version/{year}.2", response.url)

    def test_approve_policy_version_increment(self):
        """Approving multiple drafts increments version correctly."""
        self.client.force_login(self.user)
        year = datetime.now().year
        draft1 = PrivacyPolicy.objects.create(
            text="Draft 1", approved=False, changelog="Changelog 1"
        )
        self.client.post(
            reverse("approve-policy", kwargs={"draft_uuid": draft1.draft_uuid})
        )
        draft1.refresh_from_db()
        self.assertEqual(draft1.version, f"{year}.2")

        draft2 = PrivacyPolicy.objects.create(
            text="Draft 2", approved=False, changelog="Changelog 2"
        )
        self.client.post(
            reverse("approve-policy", kwargs={"draft_uuid": draft2.draft_uuid})
        )
        draft2.refresh_from_db()
        self.assertEqual(draft2.version, f"{year}.3")

    def test_view_version(self):
        """View version shows specific approved policy version."""
        year = datetime.now().year
        policy = PrivacyPolicy.objects.create(
            text="# Version Policy",
            version=f"{year}.5",
            approved=True,
            changelog="Version changelog",
        )
        response = self.client.get(
            reverse("view-version", kwargs={"version": f"{year}.5"})
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Version Policy")
        self.assertContains(response, f"{year}.5")
        self.assertContains(response, "Version changelog")

    def test_view_version_not_found(self):
        """Viewing non-existent version returns 404."""
        response = self.client.get(
            reverse("view-version", kwargs={"version": "2025.999"})
        )
        self.assertEqual(response.status_code, 404)

    def test_view_version_shows_latest_indicator(self):
        """View version shows if it's the latest."""
        year = datetime.now().year
        latest = PrivacyPolicy.objects.create(
            text="# Latest",
            version=f"{year}.10",
            approved=True,
            changelog="",
        )
        response = self.client.get(
            reverse("view-version", kwargs={"version": f"{year}.10"})
        )
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "not the latest")

    def test_latest_version_only_approved(self):
        """latest_version only returns approved policies."""
        year = datetime.now().year
        PrivacyPolicy.objects.create(
            text="Draft", approved=False, changelog=""
        )
        approved = PrivacyPolicy.objects.create(
            text="Approved",
            version=f"{year}.2",
            approved=True,
            changelog="",
        )
        latest = PrivacyPolicy.latest_version()
        self.assertEqual(latest, approved)

    def test_latest_text_only_approved(self):
        """latest_text only returns text from approved policies."""
        year = datetime.now().year
        PrivacyPolicy.objects.create(text="Draft", approved=False, changelog="")
        approved = PrivacyPolicy.objects.create(
            text="Approved text",
            version=f"{year}.3",
            approved=True,
            changelog="",
        )
        text = PrivacyPolicy.latest_text()
        self.assertEqual(text, "Approved text")
