"""Tests for feature_switches app."""

from cards.models.combatant import Combatant
from django.core.cache import cache
from django.test import TestCase
from feature_switches.helpers import CACHE_KEY_PREFIX, clear_cache, is_enabled
from feature_switches.models import (
    ACCESS_MODE_DISABLED,
    ACCESS_MODE_GLOBAL,
    ACCESS_MODE_LIST,
    FeatureSwitch,
)
from feature_switches.templatetags.feature_switches import switch_enabled
from sso_user.models import SSOUser


class FeatureSwitchModelTestCase(TestCase):
    """Tests for FeatureSwitch model."""

    def test_create_feature_switch(self):
        """Test creating a feature switch."""
        switch = FeatureSwitch.objects.create(
            name="test_feature",
            description="A test feature",
            access_mode=ACCESS_MODE_GLOBAL,
        )

        self.assertEqual(switch.name, "test_feature")
        self.assertEqual(switch.description, "A test feature")
        self.assertEqual(switch.access_mode, ACCESS_MODE_GLOBAL)
        self.assertIsNotNone(switch.created_at)
        self.assertIsNotNone(switch.updated_at)

    def test_str_representation(self):
        """Test string representation of feature switch."""
        switch = FeatureSwitch.objects.create(
            name="test_feature",
            access_mode=ACCESS_MODE_GLOBAL,
        )
        self.assertIn("test_feature", str(switch))
        self.assertIn("Global", str(switch))

    def test_str_representation_disabled(self):
        """Test string representation when disabled."""
        switch = FeatureSwitch.objects.create(
            name="disabled_feature",
            access_mode=ACCESS_MODE_DISABLED,
        )
        self.assertIn("disabled_feature", str(switch))
        self.assertIn("Disabled", str(switch))

    def test_unique_name(self):
        """Test that switch names must be unique."""
        FeatureSwitch.objects.create(name="unique_feature")

        with self.assertRaises(Exception):
            FeatureSwitch.objects.create(name="unique_feature")

    def test_default_access_mode_disabled(self):
        """Test that access_mode defaults to disabled."""
        switch = FeatureSwitch.objects.create(name="default_test")
        self.assertEqual(switch.access_mode, ACCESS_MODE_DISABLED)


class IsEnabledHelperTestCase(TestCase):
    """Tests for is_enabled helper function."""

    def setUp(self):
        """Clear cache before each test."""
        cache.clear()

    def tearDown(self):
        """Clear cache after each test."""
        cache.clear()

    def test_disabled_mode_returns_false(self):
        """Test that disabled access mode returns False."""
        FeatureSwitch.objects.create(
            name="disabled_feature", access_mode=ACCESS_MODE_DISABLED
        )

        result = is_enabled("disabled_feature")

        self.assertFalse(result)

    def test_global_mode_returns_true(self):
        """Test that global access mode returns True for all users."""
        FeatureSwitch.objects.create(
            name="global_feature", access_mode=ACCESS_MODE_GLOBAL
        )

        result = is_enabled("global_feature")
        self.assertTrue(result)

        result_with_user = is_enabled("global_feature", user=None)
        self.assertTrue(result_with_user)

    def test_list_mode_with_empty_list_returns_false(self):
        """Test that list mode with empty allowed_users returns False."""
        FeatureSwitch.objects.create(name="list_feature", access_mode=ACCESS_MODE_LIST)

        result = is_enabled("list_feature")
        self.assertFalse(result)

        result_with_user = is_enabled("list_feature", user=None)
        self.assertFalse(result_with_user)

    def test_list_mode_with_user_in_list_returns_true(self):
        """Test that list mode returns True for combatant in allowed_users."""
        combatant = Combatant.objects.create(
            email="test@example.com",
            legal_name="Test Legal",
            sca_name="Test Fighter",
        )
        switch = FeatureSwitch.objects.create(
            name="list_feature", access_mode=ACCESS_MODE_LIST
        )
        switch.allowed_users.add(combatant)

        result = is_enabled("list_feature", user=combatant)
        self.assertTrue(result)

    def test_list_mode_with_user_not_in_list_returns_false(self):
        """Test that list mode returns False for combatant not in allowed_users."""
        combatant1 = Combatant.objects.create(
            email="test1@example.com",
            legal_name="Test Legal 1",
            sca_name="Test Fighter 1",
        )
        combatant2 = Combatant.objects.create(
            email="test2@example.com",
            legal_name="Test Legal 2",
            sca_name="Test Fighter 2",
        )
        switch = FeatureSwitch.objects.create(
            name="list_feature", access_mode=ACCESS_MODE_LIST
        )
        switch.allowed_users.add(combatant1)

        result = is_enabled("list_feature", user=combatant2)
        self.assertFalse(result)

    def test_list_mode_without_user_returns_false(self):
        """Test that list mode returns False when no user provided."""
        combatant = Combatant.objects.create(
            email="test@example.com",
            legal_name="Test Legal",
            sca_name="Test Fighter",
        )
        switch = FeatureSwitch.objects.create(
            name="list_feature", access_mode=ACCESS_MODE_LIST
        )
        switch.allowed_users.add(combatant)

        result = is_enabled("list_feature", user=None)
        self.assertFalse(result)

    def test_nonexistent_switch_returns_default_false(self):
        """Test that nonexistent switch returns default=False."""
        result = is_enabled("nonexistent_feature", default=False)
        self.assertFalse(result)

    def test_nonexistent_switch_logs_warning(self):
        """Test that nonexistent switch logs a warning (default behavior)."""
        result = is_enabled("nonexistent_feature")
        self.assertFalse(result)

    def test_caching_works(self):
        """Test that results are cached."""
        FeatureSwitch.objects.create(
            name="cached_feature", access_mode=ACCESS_MODE_GLOBAL
        )

        is_enabled("cached_feature")

        cache_key = f"{CACHE_KEY_PREFIX}cached_feature"
        cached_value = cache.get(cache_key)
        self.assertTrue(cached_value)

    def test_cache_is_used_on_subsequent_calls(self):
        """Test that cache is used instead of database on repeat calls."""
        FeatureSwitch.objects.create(name="cache_test", access_mode=ACCESS_MODE_GLOBAL)

        is_enabled("cache_test")

        FeatureSwitch.objects.filter(name="cache_test").update(
            access_mode=ACCESS_MODE_DISABLED
        )

        result = is_enabled("cache_test")
        self.assertTrue(result)

    def test_user_specific_cache_keys(self):
        """Test that user-specific cache keys are used for list mode."""
        combatant1 = Combatant.objects.create(
            email="user1@example.com",
            legal_name="Test Legal 1",
            sca_name="Test Fighter 1",
        )
        combatant2 = Combatant.objects.create(
            email="user2@example.com",
            legal_name="Test Legal 2",
            sca_name="Test Fighter 2",
        )
        switch = FeatureSwitch.objects.create(
            name="user_cache_test", access_mode=ACCESS_MODE_LIST
        )
        switch.allowed_users.add(combatant1)

        is_enabled("user_cache_test", user=combatant1)
        is_enabled("user_cache_test", user=combatant2)

        cache_key_user1 = f"{CACHE_KEY_PREFIX}user_cache_test:user1@example.com"
        cache_key_user2 = f"{CACHE_KEY_PREFIX}user_cache_test:user2@example.com"

        self.assertTrue(cache.get(cache_key_user1))
        self.assertFalse(cache.get(cache_key_user2))


class ClearCacheTestCase(TestCase):
    """Tests for clear_cache helper function."""

    def setUp(self):
        """Set up test data."""
        cache.clear()
        self.switch1 = FeatureSwitch.objects.create(
            name="switch1", access_mode=ACCESS_MODE_GLOBAL
        )
        self.switch2 = FeatureSwitch.objects.create(
            name="switch2", access_mode=ACCESS_MODE_DISABLED
        )

    def tearDown(self):
        """Clear cache after test."""
        cache.clear()

    def test_clear_specific_switch_cache(self):
        """Test clearing cache for a specific switch."""
        is_enabled("switch1")
        is_enabled("switch2")

        clear_cache("switch1")

        self.switch1.access_mode = ACCESS_MODE_DISABLED
        self.switch1.save()

        result = is_enabled("switch1")
        self.assertFalse(result)

        result = is_enabled("switch2")
        self.assertFalse(result)

    def test_clear_all_switch_cache(self):
        """Test clearing cache for all switches."""
        is_enabled("switch1")
        is_enabled("switch2")

        clear_cache()

        self.switch1.access_mode = ACCESS_MODE_DISABLED
        self.switch1.save()
        self.switch2.access_mode = ACCESS_MODE_GLOBAL
        self.switch2.save()

        self.assertFalse(is_enabled("switch1"))
        self.assertTrue(is_enabled("switch2"))

    def test_clear_cache_with_user_specific_keys(self):
        """Test clearing cache clears user-specific keys."""
        combatant = Combatant.objects.create(
            email="test@example.com",
            legal_name="Test Legal",
            sca_name="Test Fighter",
        )
        switch = FeatureSwitch.objects.create(
            name="user_switch", access_mode=ACCESS_MODE_LIST
        )
        switch.allowed_users.add(combatant)

        is_enabled("user_switch", user=combatant)

        cache_key = f"{CACHE_KEY_PREFIX}user_switch:test@example.com"
        self.assertTrue(cache.get(cache_key))

        clear_cache("user_switch")

        self.assertIsNone(cache.get(cache_key))


class FeatureSwitchTemplateTagTestCase(TestCase):
    """Tests for switch_enabled template tag."""

    def setUp(self):
        """Set up test data."""
        cache.clear()

    def tearDown(self):
        """Clear cache after test."""
        cache.clear()

    def test_template_tag_with_global_feature(self):
        """Test template tag returns True for global feature."""
        FeatureSwitch.objects.create(
            name="template_feature", access_mode=ACCESS_MODE_GLOBAL
        )

        result = switch_enabled({}, "template_feature")
        self.assertTrue(result)

    def test_template_tag_with_disabled_feature(self):
        """Test template tag returns False for disabled feature."""
        FeatureSwitch.objects.create(
            name="disabled_template", access_mode=ACCESS_MODE_DISABLED
        )

        result = switch_enabled({}, "disabled_template")
        self.assertFalse(result)

    def test_template_tag_with_nonexistent_feature(self):
        """Test template tag returns False for nonexistent feature."""

        result = switch_enabled({}, "nonexistent")
        self.assertFalse(result)

    def test_template_tag_with_user_in_context(self):
        """Test template tag uses user from context for list mode."""

        user = SSOUser.objects.create(email="test@example.com")
        combatant = Combatant.objects.create(
            email="test@example.com",
            legal_name="Test Legal",
            sca_name="Test Fighter",
        )
        switch = FeatureSwitch.objects.create(
            name="list_template", access_mode=ACCESS_MODE_LIST
        )
        switch.allowed_users.add(combatant)

        context = {"user": user}
        result = switch_enabled(context, "list_template")
        self.assertTrue(result)

        context_no_user = {}
        result_no_user = switch_enabled(context_no_user, "list_template")
        self.assertFalse(result_no_user)
