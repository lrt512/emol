"""Tests for feature_switches app."""

from django.core.cache import cache
from django.test import TestCase

from .helpers import CACHE_KEY_PREFIX, clear_cache, is_enabled
from .models import FeatureSwitch


class FeatureSwitchModelTestCase(TestCase):
    """Tests for FeatureSwitch model."""

    def test_create_feature_switch(self):
        """Test creating a feature switch."""
        switch = FeatureSwitch.objects.create(
            name="test_feature",
            description="A test feature",
            enabled=True,
        )

        self.assertEqual(switch.name, "test_feature")
        self.assertEqual(switch.description, "A test feature")
        self.assertTrue(switch.enabled)
        self.assertIsNotNone(switch.created_at)
        self.assertIsNotNone(switch.updated_at)

    def test_str_representation(self):
        """Test string representation of feature switch."""
        switch = FeatureSwitch.objects.create(
            name="test_feature",
            enabled=True,
        )
        self.assertIn("test_feature", str(switch))
        self.assertIn("ON", str(switch))

    def test_str_representation_disabled(self):
        """Test string representation when disabled."""
        switch = FeatureSwitch.objects.create(
            name="disabled_feature",
            enabled=False,
        )
        self.assertIn("disabled_feature", str(switch))
        self.assertIn("OFF", str(switch))

    def test_unique_name(self):
        """Test that switch names must be unique."""
        FeatureSwitch.objects.create(name="unique_feature")

        with self.assertRaises(Exception):
            FeatureSwitch.objects.create(name="unique_feature")

    def test_default_enabled_false(self):
        """Test that enabled defaults to False."""
        switch = FeatureSwitch.objects.create(name="default_test")
        self.assertFalse(switch.enabled)


class IsEnabledHelperTestCase(TestCase):
    """Tests for is_enabled helper function."""

    def setUp(self):
        """Clear cache before each test."""
        cache.clear()

    def tearDown(self):
        """Clear cache after each test."""
        cache.clear()

    def test_enabled_switch_returns_true(self):
        """Test that enabled switch returns True."""
        FeatureSwitch.objects.create(name="enabled_feature", enabled=True)

        result = is_enabled("enabled_feature")

        self.assertTrue(result)

    def test_disabled_switch_returns_false(self):
        """Test that disabled switch returns False."""
        FeatureSwitch.objects.create(name="disabled_feature", enabled=False)

        result = is_enabled("disabled_feature")

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
        FeatureSwitch.objects.create(name="cached_feature", enabled=True)

        is_enabled("cached_feature")

        cache_key = f"{CACHE_KEY_PREFIX}cached_feature"
        cached_value = cache.get(cache_key)
        self.assertTrue(cached_value)

    def test_cache_is_used_on_subsequent_calls(self):
        """Test that cache is used instead of database on repeat calls."""
        FeatureSwitch.objects.create(name="cache_test", enabled=True)

        is_enabled("cache_test")

        FeatureSwitch.objects.filter(name="cache_test").update(enabled=False)

        result = is_enabled("cache_test")
        self.assertTrue(result)


class ClearCacheTestCase(TestCase):
    """Tests for clear_cache helper function."""

    def setUp(self):
        """Set up test data."""
        cache.clear()
        self.switch1 = FeatureSwitch.objects.create(name="switch1", enabled=True)
        self.switch2 = FeatureSwitch.objects.create(name="switch2", enabled=False)

    def tearDown(self):
        """Clear cache after test."""
        cache.clear()

    def test_clear_specific_switch_cache(self):
        """Test clearing cache for a specific switch."""
        is_enabled("switch1")
        is_enabled("switch2")

        clear_cache("switch1")

        self.switch1.enabled = False
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

        self.switch1.enabled = False
        self.switch1.save()
        self.switch2.enabled = True
        self.switch2.save()

        self.assertFalse(is_enabled("switch1"))
        self.assertTrue(is_enabled("switch2"))


class FeatureSwitchTemplateTagTestCase(TestCase):
    """Tests for switch_enabled template tag."""

    def setUp(self):
        """Set up test data."""
        cache.clear()

    def tearDown(self):
        """Clear cache after test."""
        cache.clear()

    def test_template_tag_with_enabled_feature(self):
        """Test template tag returns True for enabled feature."""
        FeatureSwitch.objects.create(name="template_feature", enabled=True)

        from .templatetags.feature_switches import switch_enabled

        result = switch_enabled("template_feature")
        self.assertTrue(result)

    def test_template_tag_with_disabled_feature(self):
        """Test template tag returns False for disabled feature."""
        FeatureSwitch.objects.create(name="disabled_template", enabled=False)

        from .templatetags.feature_switches import switch_enabled

        result = switch_enabled("disabled_template")
        self.assertFalse(result)

    def test_template_tag_with_nonexistent_feature(self):
        """Test template tag returns False for nonexistent feature."""
        from .templatetags.feature_switches import switch_enabled

        result = switch_enabled("nonexistent")
        self.assertFalse(result)
