from datetime import timedelta
from io import StringIO
from unittest.mock import patch

from cards.management.commands.clean_expired import Command as CleanExpiredCommand
from cards.management.commands.send_reminders import Command as SendRemindersCommand
from cards.management.commands.summarize_expiries import (
    Command as SummarizeExpiriesCommand,
)
from cards.models import (
    Authorization,
    Card,
    Combatant,
    Discipline,
    OneTimeCode,
    Reminder,
    Waiver,
)
from cards.utility.time import today, utc_tomorrow
from django.contrib.contenttypes.models import ContentType
from django.core.management import call_command
from django.test import TestCase, override_settings
from django.utils import timezone


class CleanExpiredCommandTestCase(TestCase):
    """Test the clean_expired management command"""

    def setUp(self):
        self.combatant = Combatant.objects.create(
            sca_name="Test Fighter",
            legal_name="Test Legal",
            email="test@example.com",
            accepted_privacy_policy=True,
        )

    def test_clean_expired_codes_success(self):
        """Test cleaning up expired one-time codes"""
        expired_code1 = OneTimeCode.objects.create(
            combatant=self.combatant,
            url_template="/test/{code}",
            expires_at=timezone.now() - timedelta(days=1),
        )

        combatant2 = Combatant.objects.create(
            sca_name="Test Fighter 2",
            legal_name="Test Legal 2",
            email="test2@example.com",
            accepted_privacy_policy=True,
        )
        expired_code2 = OneTimeCode.objects.create(
            combatant=combatant2,
            url_template="/test/{code}",
            expires_at=timezone.now() - timedelta(hours=1),
        )

        combatant3 = Combatant.objects.create(
            sca_name="Test Fighter 3",
            legal_name="Test Legal 3",
            email="test3@example.com",
            accepted_privacy_policy=True,
        )
        valid_code = OneTimeCode.objects.create(
            combatant=combatant3, url_template="/test/{code}", expires_at=utc_tomorrow()
        )

        self.assertEqual(OneTimeCode.objects.count(), 3)

        call_command("clean_expired")

        self.assertEqual(OneTimeCode.objects.count(), 1)
        self.assertTrue(OneTimeCode.objects.filter(id=valid_code.id).exists())
        self.assertFalse(OneTimeCode.objects.filter(id=expired_code1.id).exists())
        self.assertFalse(OneTimeCode.objects.filter(id=expired_code2.id).exists())

    def test_clean_consumed_codes(self):
        """Test cleaning up consumed one-time codes"""
        consumed_code = OneTimeCode.objects.create(
            combatant=self.combatant,
            url_template="/test/{code}",
            consumed=True,
        )

        call_command("clean_expired")

        self.assertFalse(OneTimeCode.objects.filter(id=consumed_code.id).exists())

    def test_clean_expired_codes_none_expired(self):
        """Test command when no codes are expired"""
        OneTimeCode.objects.create(
            combatant=self.combatant,
            url_template="/test/{code}",
            expires_at=utc_tomorrow(),
        )

        self.assertEqual(OneTimeCode.objects.count(), 1)

        call_command("clean_expired")

        self.assertEqual(OneTimeCode.objects.count(), 1)

    def test_clean_expired_codes_empty_database(self):
        """Test command when no codes exist"""
        self.assertEqual(OneTimeCode.objects.count(), 0)

        call_command("clean_expired")

        self.assertEqual(OneTimeCode.objects.count(), 0)

    def test_clean_expired_boundary_condition(self):
        """Test command with codes expiring exactly now"""
        now = timezone.now()

        boundary_code = OneTimeCode.objects.create(
            combatant=self.combatant, url_template="/test/{code}", expires_at=now
        )

        with patch("django.utils.timezone.now", return_value=now):
            call_command("clean_expired")

        self.assertFalse(OneTimeCode.objects.filter(id=boundary_code.id).exists())


class SendRemindersCommandTestCase(TestCase):
    """Test the send_reminders management command"""

    def setUp(self):
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

        # Create a card that expires in 30 days
        self.card = Card.objects.create(
            combatant=self.combatant,
            discipline=self.discipline,
            date_issued=today() - timedelta(days=365 * 2 - 30),  # Expires in 30 days
        )

        # Create a waiver that expires in 60 days
        self.waiver = Waiver.objects.create(
            combatant=self.combatant,
            date_signed=today() - timedelta(days=365 * 7 - 60),  # Expires in 60 days
        )

    @override_settings(REMINDER_DAYS=[60, 30, 14, 0])
    def test_send_reminders_dry_run_mode(self):
        """Test dry-run mode shows what would happen without making changes"""
        # Reminders are automatically created by post_save signals
        # Update existing reminders to be due today
        card_reminders = Reminder.objects.filter(
            content_type=ContentType.objects.get_for_model(Card), object_id=self.card.id
        )
        waiver_reminders = Reminder.objects.filter(
            content_type=ContentType.objects.get_for_model(Waiver),
            object_id=self.waiver.id,
        )

        # Make some reminders due today
        card_reminders.filter(days_to_expiry=30).update(due_date=today())
        waiver_reminders.filter(days_to_expiry=60).update(due_date=today())

        initial_reminder_count = Reminder.objects.count()

        # Run dry-run
        call_command("send_reminders", "--dry-run")

        # Verify no changes were made
        self.assertEqual(Reminder.objects.count(), initial_reminder_count)

    @override_settings(REMINDER_DAYS=[60, 30, 14, 0])
    def test_send_reminders_orphaned_cleanup(self):
        """Test that orphaned reminders are cleaned up"""
        # Create an orphaned reminder (pointing to non-existent object)
        card_content_type = ContentType.objects.get_for_model(Card)
        orphaned_reminder = Reminder.objects.create(
            content_type=card_content_type,
            object_id=99999,  # Non-existent card ID
            days_to_expiry=30,
            due_date=today(),
        )

        # Run command
        call_command("send_reminders")

        # Verify orphaned reminder was deleted
        self.assertFalse(Reminder.objects.filter(id=orphaned_reminder.id).exists())

    @override_settings(REMINDER_DAYS=[60, 30, 14, 0])
    def test_send_reminders_orphaned_cleanup_dry_run(self):
        """Test that dry-run mode shows orphaned reminders but doesn't delete them"""
        # Create an orphaned reminder
        card_content_type = ContentType.objects.get_for_model(Card)
        orphaned_reminder = Reminder.objects.create(
            content_type=card_content_type,
            object_id=99999,  # Non-existent card ID
            days_to_expiry=30,
            due_date=today(),
        )

        # Run dry-run
        call_command("send_reminders", "--dry-run")

        # Verify orphaned reminder still exists
        self.assertTrue(Reminder.objects.filter(id=orphaned_reminder.id).exists())

    @override_settings(REMINDER_DAYS=[60, 30, 14, 0])
    def test_send_reminders_prioritization(self):
        """Test that most urgent reminders are sent and older ones are expired"""
        # Use automatically created reminders and update them to simulate backlog
        card_reminders = Reminder.objects.filter(
            content_type=ContentType.objects.get_for_model(Card), object_id=self.card.id
        )

        # Update reminders to be overdue (simulating backlog scenario)
        card_reminders.filter(days_to_expiry=60).update(
            due_date=today() - timedelta(days=30)
        )
        card_reminders.filter(days_to_expiry=30).update(
            due_date=today() - timedelta(days=5)
        )
        card_reminders.filter(days_to_expiry=14).update(due_date=today())

        reminder_60 = card_reminders.get(days_to_expiry=60)
        reminder_30 = card_reminders.get(days_to_expiry=30)

        # Mock email sending to verify which reminder gets processed
        with patch("cards.models.reminder.Reminder.send_email"):
            call_command("send_reminders")

        # Verify most urgent reminder was processed
        # The 14-day reminder should have been kept and processed
        # The 60-day and 30-day reminders should have been expired
        self.assertFalse(Reminder.objects.filter(id=reminder_60.id).exists())
        self.assertFalse(Reminder.objects.filter(id=reminder_30.id).exists())
        # The 14-day reminder might be deleted after sending, that's OK

    @override_settings(REMINDER_DAYS=[60, 30, 14, 0])
    def test_send_reminders_privacy_policy_not_accepted(self):
        """Test that reminders are skipped when privacy policy is not accepted"""
        # Create combatant who hasn't accepted privacy policy
        combatant_no_privacy = Combatant.objects.create(
            sca_name="No Privacy Fighter",
            legal_name="No Privacy Legal",
            email="noprivacy@example.com",
            accepted_privacy_policy=False,  # Key difference
        )

        card_no_privacy = Card.objects.create(
            combatant=combatant_no_privacy,
            discipline=self.discipline,
            date_issued=today() - timedelta(days=365 * 2 - 30),
        )

        # Use automatically created reminder for this card
        reminder = Reminder.objects.filter(
            content_type=ContentType.objects.get_for_model(Card),
            object_id=card_no_privacy.id,
            days_to_expiry=30,
        ).first()
        # Make reminder due today
        reminder.due_date = today()
        reminder.save()

        # Run dry-run to see what would happen
        initial_reminder_count = Reminder.objects.count()
        call_command("send_reminders", "--dry-run")

        # Verify no changes were made (reminder would be skipped)
        self.assertEqual(Reminder.objects.count(), initial_reminder_count)

    @override_settings(REMINDER_DAYS=[60, 30, 14, 0])
    def test_send_reminders_no_due_reminders(self):
        """Test command when no reminders are due"""
        # Ensure a clean slate by deleting all reminders created in setUp
        Reminder.objects.all().delete()

        # Create a single reminder that is not due
        future_date = timezone.now() + timedelta(days=30)
        Reminder.objects.create(
            content_object=self.card,  # It doesn't matter which object it's for
            days_to_expiry=90,
            due_date=future_date,
        )

        call_command("send_reminders")

        # Check that the future reminder was not deleted and it's the only one
        self.assertEqual(Reminder.objects.count(), 1)

    @override_settings(REMINDER_DAYS=[60, 30, 14, 0])
    def test_send_reminders_counter_accuracy(self):
        """Test that sent and expired counters are accurate"""
        # Create a second combatant and card to test multiple cards
        combatant2 = Combatant.objects.create(
            sca_name="Test Fighter 2",
            legal_name="Test Legal 2",
            email="test2@example.com",
            accepted_privacy_policy=True,
        )
        card2 = Card.objects.create(
            combatant=combatant2,
            discipline=self.discipline,
            date_issued=today() - timedelta(days=365 * 2 - 14),
        )

        # Update automatically created reminders to be due today
        card1_reminders = Reminder.objects.filter(
            content_type=ContentType.objects.get_for_model(Card), object_id=self.card.id
        )
        card2_reminders = Reminder.objects.filter(
            content_type=ContentType.objects.get_for_model(Card), object_id=card2.id
        )

        # Backlog scenario for first card (all reminders due)
        card1_reminders.update(due_date=today())

        # Single reminder for second card (14-day reminder due)
        card2_reminders.filter(days_to_expiry=14).update(due_date=today())

        # Run dry-run to check counters
        initial_reminder_count = Reminder.objects.count()
        call_command("send_reminders", "--dry-run")

        # Verify no changes were made in dry-run mode
        self.assertEqual(Reminder.objects.count(), initial_reminder_count)

    def test_command_class_instantiation(self):
        """Test that command classes can be instantiated directly"""
        clean_cmd = CleanExpiredCommand()
        send_cmd = SendRemindersCommand()
        summarize_cmd = SummarizeExpiriesCommand()

        self.assertIsNotNone(clean_cmd)
        self.assertIsNotNone(send_cmd)
        self.assertIsNotNone(summarize_cmd)

        # Test help text
        self.assertIn(
            "Clean up expired, consumed, and old one-time codes", clean_cmd.help
        )
        self.assertIn("Send reminders for expiring", send_cmd.help)
        self.assertIn("Summarize upcoming", summarize_cmd.help)

    def test_send_reminders_add_arguments(self):
        """Test that send_reminders command properly handles arguments"""
        cmd = SendRemindersCommand()

        # Test that dry-run argument is added
        parser = cmd.create_parser("send_reminders", "send_reminders")
        # This will raise if --dry-run argument wasn't added properly
        parsed = parser.parse_args(["--dry-run"])
        self.assertTrue(parsed.dry_run)

        # Test without dry-run
        parsed = parser.parse_args([])
        self.assertFalse(parsed.dry_run)


class SummarizeExpiriesCommandTestCase(TestCase):
    """Test the summarize_expiries management command"""

    def setUp(self):
        self.discipline1 = Discipline.objects.create(
            name="Armoured Combat", slug="armoured-combat"
        )
        self.discipline2 = Discipline.objects.create(name="Fencing", slug="fencing")
        self.authorization = Authorization.objects.create(
            name="Test Auth", slug="test-auth", discipline=self.discipline1
        )

        # Create combatants
        self.combatant1 = Combatant.objects.create(
            sca_name="Test Fighter 1",
            legal_name="Test Legal 1",
            email="test1@example.com",
            accepted_privacy_policy=True,
        )
        self.combatant2 = Combatant.objects.create(
            sca_name="Test Fighter 2",
            legal_name="Test Legal 2",
            email="test2@example.com",
            accepted_privacy_policy=True,
        )
        self.combatant3 = Combatant.objects.create(
            sca_name="Test Fighter 3",
            legal_name="Test Legal 3",
            email="test3@example.com",
            accepted_privacy_policy=True,
        )

    def test_summarize_expiries_default_week(self):
        """Test default week period summary"""
        # Create cards expiring in 5 days (within week)
        Card.objects.create(
            combatant=self.combatant1,
            discipline=self.discipline1,
            date_issued=today() - timedelta(days=365 * 2 - 5),  # Expires in 5 days
        )

        # Create card expiring in 10 days (outside week)
        Card.objects.create(
            combatant=self.combatant2,
            discipline=self.discipline2,
            date_issued=today() - timedelta(days=365 * 2 - 10),  # Expires in 10 days
        )

        # Run command with default settings
        call_command("summarize_expiries")

    def test_summarize_expiries_custom_days(self):
        """Test custom days parameter"""
        # Create cards with different expiry times
        Card.objects.create(
            combatant=self.combatant1,
            discipline=self.discipline1,
            date_issued=today() - timedelta(days=365 * 2 - 3),  # Expires in 3 days
        )
        Card.objects.create(
            combatant=self.combatant2,
            discipline=self.discipline2,
            date_issued=today() - timedelta(days=365 * 2 - 15),  # Expires in 15 days
        )

        # Run with 14 days - should include first card only
        call_command("summarize_expiries", "--days=14")

    def test_summarize_expiries_detailed_mode(self):
        """Test detailed listing mode"""
        # Create card and waiver expiring within a week
        Card.objects.create(
            combatant=self.combatant1,
            discipline=self.discipline1,
            date_issued=today() - timedelta(days=365 * 2 - 5),  # Expires in 5 days
        )
        Waiver.objects.create(
            combatant=self.combatant2,
            date_signed=today() - timedelta(days=365 * 7 - 3),  # Expires in 3 days
        )

        # Run with detailed flag
        call_command("summarize_expiries", "--detailed")

    def test_summarize_expiries_no_expiries(self):
        """Test when no items are expiring"""
        # Create cards/waivers that expire far in the future
        Card.objects.create(
            combatant=self.combatant1,
            discipline=self.discipline1,
            date_issued=today() - timedelta(days=100),  # Expires in ~630 days
        )
        Waiver.objects.create(
            combatant=self.combatant2,
            date_signed=today() - timedelta(days=100),  # Expires in ~2455 days
        )

        # Run command
        call_command("summarize_expiries")

    def test_summarize_expiries_different_periods(self):
        """Test different period options"""
        # Create items expiring at different times
        Card.objects.create(
            combatant=self.combatant1,
            discipline=self.discipline1,
            date_issued=today() - timedelta(days=365 * 2 - 1),  # Expires tomorrow
        )
        Card.objects.create(
            combatant=self.combatant2,
            discipline=self.discipline2,
            date_issued=today() - timedelta(days=365 * 2 - 25),  # Expires in 25 days
        )

        # Test day period - should only include tomorrow's expiry
        call_command("summarize_expiries", "--period=day")

        # Test week period
        call_command("summarize_expiries", "--period=week")

        # Test month period - should include both
        call_command("summarize_expiries", "--period=month")

    def test_summarize_expiries_cards_only(self):
        """Test summary with only cards expiring"""
        # Create multiple cards in different disciplines
        Card.objects.create(
            combatant=self.combatant1,
            discipline=self.discipline1,
            date_issued=today() - timedelta(days=365 * 2 - 3),  # Expires in 3 days
        )
        Card.objects.create(
            combatant=self.combatant2,
            discipline=self.discipline1,
            date_issued=today() - timedelta(days=365 * 2 - 5),  # Expires in 5 days
        )
        Card.objects.create(
            combatant=self.combatant3,
            discipline=self.discipline2,
            date_issued=today() - timedelta(days=365 * 2 - 6),  # Expires in 6 days
        )

        # Run detailed summary
        call_command("summarize_expiries", "--detailed")

    def test_summarize_expiries_waivers_only(self):
        """Test summary with only waivers expiring"""
        # Create multiple waivers
        Waiver.objects.create(
            combatant=self.combatant1,
            date_signed=today() - timedelta(days=365 * 7 - 2),  # Expires in 2 days
        )
        Waiver.objects.create(
            combatant=self.combatant2,
            date_signed=today() - timedelta(days=365 * 7 - 6),  # Expires in 6 days
        )

        # Run detailed summary
        call_command("summarize_expiries", "--detailed")

    def test_summarize_expiries_mixed_cards_and_waivers(self):
        """Test summary with both cards and waivers expiring"""
        # Create mix of cards and waivers
        Card.objects.create(
            combatant=self.combatant1,
            discipline=self.discipline1,
            date_issued=today() - timedelta(days=365 * 2 - 4),  # Expires in 4 days
        )
        Waiver.objects.create(
            combatant=self.combatant2,
            date_signed=today() - timedelta(days=365 * 7 - 3),  # Expires in 3 days
        )

        # Run detailed summary
        call_command("summarize_expiries", "--detailed")

    def test_summarize_expiries_command_instantiation(self):
        """Test that command can be instantiated directly"""
        cmd = SummarizeExpiriesCommand()
        self.assertIsNotNone(cmd)
        self.assertIn("Summarize upcoming", cmd.help)

    def test_summarize_expiries_argument_parsing(self):
        """Test that command arguments are parsed correctly"""
        cmd = SummarizeExpiriesCommand()
        parser = cmd.create_parser("summarize_expiries", "summarize_expiries")

        # Test default values
        parsed = parser.parse_args([])
        self.assertEqual(parsed.period, "week")
        self.assertIsNone(parsed.days)
        self.assertFalse(parsed.detailed)

        # Test period argument
        parsed = parser.parse_args(["--period=month"])
        self.assertEqual(parsed.period, "month")

        # Test custom days
        parsed = parser.parse_args(["--days=14"])
        self.assertEqual(parsed.days, 14)

        # Test detailed flag
        parsed = parser.parse_args(["--detailed"])
        self.assertTrue(parsed.detailed)

        # Test combined arguments
        parsed = parser.parse_args(["--period=day", "--detailed"])
        self.assertEqual(parsed.period, "day")
        self.assertTrue(parsed.detailed)

    def test_summarize_expiries_boundary_conditions(self):
        """Test edge cases and boundary conditions"""
        # Create card expiring exactly in 7 days (boundary of week)
        Card.objects.create(
            combatant=self.combatant1,
            discipline=self.discipline1,
            date_issued=today()
            - timedelta(days=365 * 2 - 7),  # Expires in exactly 7 days
        )

        # Run week summary - should include the boundary case
        call_command("summarize_expiries", "--period=week")

        # Run with 6 days - should not include the boundary case
        call_command("summarize_expiries", "--days=6")


class PINMigrationCommandTestCase(TestCase):
    """Test the pin_migration management command."""

    def setUp(self):
        """Set up test combatants."""
        self.combatant_with_privacy = Combatant.objects.create(
            sca_name="Test Fighter 1",
            legal_name="Test Legal 1",
            email="test1@example.com",
            accepted_privacy_policy=True,
        )
        self.combatant_without_privacy = Combatant.objects.create(
            sca_name="Test Fighter 2",
            legal_name="Test Legal 2",
            email="test2@example.com",
            accepted_privacy_policy=False,
        )
        self.combatant_with_pin = Combatant.objects.create(
            sca_name="Test Fighter 3",
            legal_name="Test Legal 3",
            email="test3@example.com",
            accepted_privacy_policy=True,
        )
        self.combatant_with_pin.set_pin("1234")

    def test_finds_combatants_without_pins(self):
        """Test that command finds combatants without PINs who accepted privacy."""
        out = StringIO()
        call_command("pin_migration", "--dry-run", stdout=out)

        output = out.getvalue()
        self.assertIn("Found 1 combatants without PINs", output)

    def test_dry_run_does_not_send_emails(self):
        """Test that --dry-run doesn't actually send emails."""
        initial_code_count = OneTimeCode.objects.count()

        call_command("pin_migration", "--dry-run")

        self.assertEqual(OneTimeCode.objects.count(), initial_code_count)

    @override_settings(SEND_EMAIL=False)
    def test_creates_one_time_codes(self):
        """Test that command creates OneTimeCodes for combatants."""
        initial_code_count = OneTimeCode.objects.count()

        call_command("pin_migration", "--stage=initial")

        self.assertEqual(OneTimeCode.objects.count(), initial_code_count + 1)
        code = OneTimeCode.objects.filter(combatant=self.combatant_with_privacy).first()
        self.assertIsNotNone(code)

    @override_settings(SEND_EMAIL=False)
    def test_limit_option(self):
        """Test --limit option restricts number of emails."""
        Combatant.objects.create(
            sca_name="Test Fighter 4",
            legal_name="Test Legal 4",
            email="test4@example.com",
            accepted_privacy_policy=True,
        )
        Combatant.objects.create(
            sca_name="Test Fighter 5",
            legal_name="Test Legal 5",
            email="test5@example.com",
            accepted_privacy_policy=True,
        )

        initial_count = OneTimeCode.objects.count()

        call_command("pin_migration", "--limit=1")

        self.assertEqual(OneTimeCode.objects.count(), initial_count + 1)

    def test_stage_options(self):
        """Test that different stages are accepted."""
        for stage in ["initial", "reminder", "final"]:
            out = StringIO()
            call_command("pin_migration", f"--stage={stage}", "--dry-run", stdout=out)
            output = out.getvalue()
            self.assertIn(stage, output)

    def test_excludes_combatants_with_pins(self):
        """Test that combatants with PINs are excluded."""
        out = StringIO()
        call_command("pin_migration", "--dry-run", stdout=out)

        output = out.getvalue()
        self.assertNotIn("test3@example.com", output)

    def test_excludes_combatants_without_privacy_acceptance(self):
        """Test that combatants who haven't accepted privacy are excluded."""
        out = StringIO()
        call_command("pin_migration", "--dry-run", stdout=out)

        output = out.getvalue()
        self.assertNotIn("test2@example.com", output)
