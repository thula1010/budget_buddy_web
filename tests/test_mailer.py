import base64
import json
import os
import unittest
from email import policy
from email.parser import BytesParser
from unittest.mock import patch

from config import mailer


class FakeResponse:
    def __init__(self, payload, status=200):
        self.payload = payload
        self.status = status

    def read(self):
        return json.dumps(self.payload).encode("utf-8")

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False


class GmailApiMailerTest(unittest.TestCase):
    def setUp(self):
        self.gmail_env = {
            "GMAIL_CLIENT_ID": "client-id.apps.googleusercontent.com",
            "GMAIL_CLIENT_SECRET": "client-secret",
            "GMAIL_REFRESH_TOKEN": "refresh-token",
            "EMAIL_USER": "sender@example.com",
            "EMAIL_FROM": "Budget Buddy <sender@example.com>",
        }

    def test_gmail_api_refreshes_token_and_sends_mime_message(self):
        responses = [
            FakeResponse({"access_token": "access-token", "expires_in": 3600}),
            FakeResponse({"id": "gmail-message-id"}, status=200),
        ]
        requests = []

        def fake_urlopen(request, timeout):
            requests.append((request, timeout))
            return responses.pop(0)

        with (
            patch.dict(os.environ, self.gmail_env, clear=True),
            patch.object(mailer, "urlopen", side_effect=fake_urlopen),
        ):
            delivered = mailer.send_email(
                "receiver@example.com",
                "Báo cáo tuần",
                "<h1>Nội dung</h1>",
                idempotency_key="weekly-1",
            )

        self.assertTrue(delivered)
        self.assertEqual(requests[0][0].full_url, mailer.GOOGLE_TOKEN_URL)
        token_body = requests[0][0].data.decode("utf-8")
        self.assertIn("grant_type=refresh_token", token_body)
        self.assertIn("refresh_token=refresh-token", token_body)
        self.assertEqual(requests[1][0].full_url, mailer.GMAIL_SEND_URL)
        self.assertEqual(
            requests[1][0].headers["Authorization"], "Bearer access-token"
        )
        api_body = json.loads(requests[1][0].data.decode("utf-8"))
        message = BytesParser(policy=policy.default).parsebytes(
            base64.urlsafe_b64decode(api_body["raw"])
        )
        self.assertEqual(message["To"], "receiver@example.com")
        self.assertEqual(message["Subject"], "Báo cáo tuần")
        self.assertEqual(message["From"], "Budget Buddy <sender@example.com>")
        self.assertIn("@budget-buddy.local", message["Message-ID"])

    def test_gmail_api_is_preferred_over_resend_and_smtp(self):
        with (
            patch.dict(os.environ, self.gmail_env, clear=True),
            patch.object(mailer, "_send_with_gmail_api", return_value=True) as gmail,
            patch.object(mailer, "_send_with_resend") as resend,
            patch.object(mailer, "_send_with_smtp") as smtp,
        ):
            self.assertTrue(mailer.email_delivery_configured())
            self.assertTrue(mailer.send_email("to@example.com", "Subject", "<p>Hi</p>"))
        gmail.assert_called_once()
        resend.assert_not_called()
        smtp.assert_not_called()


if __name__ == "__main__":
    unittest.main()
