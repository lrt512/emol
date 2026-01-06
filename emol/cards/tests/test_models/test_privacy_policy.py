"""Tests for PrivacyPolicy model."""

from datetime import datetime

from cards.models import PrivacyPolicy
from django.core.exceptions import ValidationError
from django.test import TestCase


class PrivacyPolicyModelTestCase(TestCase):
    """Tests for PrivacyPolicy model methods."""

    def setUp(self):
        """Set up test fixtures."""
        self.year = datetime.now().year

    def test_generate_version_first_in_year(self):
        """generate_version returns YYYY.1 for first policy in year."""
        draft = PrivacyPolicy.objects.create(
            text="Test", approved=False, changelog=""
        )
        version = draft.generate_version()
        self.assertEqual(version, f"{self.year}.1")

    def test_generate_version_increments(self):
        """generate_version increments for multiple policies in same year."""
        PrivacyPolicy.objects.create(
            text="First",
            version=f"{self.year}.1",
            approved=True,
            changelog="",
        )
        PrivacyPolicy.objects.create(
            text="Second",
            version=f"{self.year}.2",
            approved=True,
            changelog="",
        )
        draft = PrivacyPolicy.objects.create(
            text="Third", approved=False, changelog=""
        )
        version = draft.generate_version()
        self.assertEqual(version, f"{self.year}.3")

    def test_generate_version_returns_existing_if_approved(self):
        """generate_version returns existing version if already approved."""
        policy = PrivacyPolicy.objects.create(
            text="Approved",
            version=f"{self.year}.5",
            approved=True,
            changelog="",
        )
        version = policy.generate_version()
        self.assertEqual(version, f"{self.year}.5")

    def test_approve_generates_version(self):
        """approve() generates version and sets approved=True."""
        draft = PrivacyPolicy.objects.create(
            text="Draft", approved=False, changelog="Test changelog"
        )
        draft.approve()
        self.assertTrue(draft.approved)
        self.assertEqual(draft.version, f"{self.year}.1")
        self.assertIsNotNone(draft.version)

    def test_approve_already_approved_raises_error(self):
        """approve() raises error if already approved."""
        policy = PrivacyPolicy.objects.create(
            text="Approved",
            version=f"{self.year}.1",
            approved=True,
            changelog="",
        )
        with self.assertRaises(ValidationError) as cm:
            policy.approve()
        self.assertIn("already approved", str(cm.exception))

    def test_save_draft_auto_generates_uuid(self):
        """Saving a draft auto-generates draft_uuid."""
        draft = PrivacyPolicy(text="Draft", approved=False, changelog="")
        draft.save()
        self.assertIsNotNone(draft.draft_uuid)

    def test_save_approved_policy_prevents_editing(self):
        """Saving an approved policy raises error."""
        policy = PrivacyPolicy.objects.create(
            text="Original",
            version=f"{self.year}.1",
            approved=True,
            changelog="",
        )
        policy.text = "Modified"
        with self.assertRaises(ValidationError) as cm:
            policy.save()
        self.assertIn("Cannot update an approved", str(cm.exception))

    def test_save_draft_allows_editing(self):
        """Saving a draft allows editing."""
        draft = PrivacyPolicy.objects.create(
            text="Original", approved=False, changelog=""
        )
        draft.text = "Modified"
        draft.save()
        draft.refresh_from_db()
        self.assertEqual(draft.text, "Modified")

    def test_latest_version_returns_highest(self):
        """latest_version returns the highest version number."""
        PrivacyPolicy.objects.create(
            text="First",
            version=f"{self.year}.1",
            approved=True,
            changelog="",
        )
        PrivacyPolicy.objects.create(
            text="Second",
            version=f"{self.year}.5",
            approved=True,
            changelog="",
        )
        PrivacyPolicy.objects.create(
            text="Third",
            version=f"{self.year}.3",
            approved=True,
            changelog="",
        )
        latest = PrivacyPolicy.latest_version()
        self.assertEqual(latest.version, f"{self.year}.5")

    def test_latest_version_ignores_drafts(self):
        """latest_version ignores draft policies."""
        PrivacyPolicy.objects.create(text="Draft", approved=False, changelog="")
        approved = PrivacyPolicy.objects.create(
            text="Approved",
            version=f"{self.year}.1",
            approved=True,
            changelog="",
        )
        latest = PrivacyPolicy.latest_version()
        self.assertEqual(latest, approved)

    def test_latest_version_returns_none_if_no_approved(self):
        """latest_version returns None if no approved policies exist."""
        PrivacyPolicy.objects.create(text="Draft", approved=False, changelog="")
        latest = PrivacyPolicy.latest_version()
        self.assertIsNone(latest)

    def test_latest_text_returns_empty_if_no_approved(self):
        """latest_text returns empty string if no approved policies."""
        PrivacyPolicy.objects.create(text="Draft", approved=False, changelog="")
        text = PrivacyPolicy.latest_text()
        self.assertEqual(text, "")

    def test_latest_text_replaces_date_placeholder(self):
        """latest_text replaces [DATE] placeholder."""
        policy = PrivacyPolicy.objects.create(
            text="Policy dated [DATE]",
            version=f"{self.year}.1",
            approved=True,
            changelog="",
        )
        text = PrivacyPolicy.latest_text()
        expected_date = policy.created_at.strftime("%Y-%m-%d")
        self.assertIn(expected_date, text)
        self.assertNotIn("[DATE]", text)

    def test_get_draft_by_uuid(self):
        """get_draft_by_uuid retrieves draft by UUID."""
        draft = PrivacyPolicy.objects.create(
            text="Draft", approved=False, changelog=""
        )
        retrieved = PrivacyPolicy.get_draft_by_uuid(draft.draft_uuid)
        self.assertEqual(retrieved, draft)

    def test_get_draft_by_uuid_returns_none_if_not_found(self):
        """get_draft_by_uuid returns None if UUID not found."""
        import uuid

        fake_uuid = uuid.uuid4()
        retrieved = PrivacyPolicy.get_draft_by_uuid(fake_uuid)
        self.assertIsNone(retrieved)

    def test_version_cross_year(self):
        """Version generation works across different years."""
        last_year = self.year - 1
        PrivacyPolicy.objects.create(
            text="Last year",
            version=f"{last_year}.5",
            approved=True,
            changelog="",
        )
        draft = PrivacyPolicy.objects.create(
            text="This year", approved=False, changelog=""
        )
        version = draft.generate_version()
        self.assertEqual(version, f"{self.year}.1")

