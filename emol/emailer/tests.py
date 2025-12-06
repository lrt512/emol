"""Tests for the AWSEmailer class."""

from unittest.mock import MagicMock, patch

from django.test import TestCase, override_settings

from emailer import AWSEmailer


class AWSEmailerTestCase(TestCase):
    """Tests for AWSEmailer.send_email()."""

    @override_settings(SEND_EMAIL=False)
    def test_send_email_disabled_returns_true(self):
        """When SEND_EMAIL is False, emails are logged but not sent."""
        result = AWSEmailer.send_email(
            recipient="test@example.com",
            subject="Test Subject",
            body="Test body",
        )

        self.assertTrue(result)

    @override_settings(
        SEND_EMAIL=True,
        MAIL_DEFAULT_SENDER="sender@example.com",
        MOL_EMAIL="mol@example.com",
    )
    @patch("emailer.get_aws_session")
    def test_send_email_success(self, mock_get_session):
        """Successful email send returns True."""
        mock_client = MagicMock()
        mock_client.send_email.return_value = {"MessageId": "test-id"}
        mock_session = MagicMock()
        mock_session.client.return_value = mock_client
        mock_get_session.return_value = mock_session

        result = AWSEmailer.send_email(
            recipient="test@example.com",
            subject="Test Subject",
            body="Test body",
        )

        self.assertTrue(result)
        mock_client.send_email.assert_called_once()
        call_args = mock_client.send_email.call_args
        self.assertEqual(
            call_args.kwargs["Destination"]["ToAddresses"], ["test@example.com"]
        )
        self.assertEqual(
            call_args.kwargs["Message"]["Subject"]["Data"], "Test Subject"
        )

    @override_settings(
        SEND_EMAIL=True,
        MAIL_DEFAULT_SENDER="sender@example.com",
        MOL_EMAIL="mol@example.com",
    )
    @patch("emailer.get_aws_session")
    def test_send_email_with_custom_from_and_reply_to(self, mock_get_session):
        """Custom from_email and reply_to are used when provided."""
        mock_client = MagicMock()
        mock_client.send_email.return_value = {"MessageId": "test-id"}
        mock_session = MagicMock()
        mock_session.client.return_value = mock_client
        mock_get_session.return_value = mock_session

        AWSEmailer.send_email(
            recipient="test@example.com",
            subject="Test",
            body="Body",
            from_email="custom@example.com",
            reply_to="reply@example.com",
        )

        call_args = mock_client.send_email.call_args
        self.assertIn("custom@example.com", call_args.kwargs["Source"])
        self.assertEqual(call_args.kwargs["ReplyToAddresses"], ["reply@example.com"])

    @override_settings(
        SEND_EMAIL=True,
        MAIL_DEFAULT_SENDER="sender@example.com",
        MOL_EMAIL="mol@example.com",
    )
    @patch("emailer.get_aws_session")
    def test_send_email_ses_error_returns_false(self, mock_get_session):
        """SES client error returns False."""
        from botocore.exceptions import ClientError

        mock_client = MagicMock()
        mock_client.send_email.side_effect = ClientError(
            {"Error": {"Code": "TestError", "Message": "Test"}}, "send_email"
        )
        mock_session = MagicMock()
        mock_session.client.return_value = mock_client
        mock_get_session.return_value = mock_session

        result = AWSEmailer.send_email(
            recipient="test@example.com",
            subject="Test",
            body="Body",
        )

        self.assertFalse(result)

