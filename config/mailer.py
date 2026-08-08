import json
import logging
import os
import smtplib
import ssl
from email.message import EmailMessage
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from dotenv import load_dotenv


load_dotenv()
logger = logging.getLogger(__name__)


def email_delivery_configured():
    resend_ready = bool(os.environ.get("RESEND_API_KEY") and os.environ.get("EMAIL_FROM"))
    smtp_user = os.environ.get("SMTP_USER") or os.environ.get("EMAIL_USER")
    smtp_password = os.environ.get("SMTP_PASSWORD") or os.environ.get("EMAIL_PASS")
    return resend_ready or bool(smtp_user and smtp_password)


def _send_with_resend(to_email, subject, html_content, idempotency_key=None):
    api_key = os.environ.get("RESEND_API_KEY")
    sender = os.environ.get("EMAIL_FROM")
    if not api_key or not sender:
        return False

    payload = json.dumps({
        "from": sender,
        "to": [to_email],
        "subject": subject,
        "html": html_content,
    }).encode("utf-8")
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "User-Agent": "Budget-Buddy/1.0",
    }
    if idempotency_key:
        headers["Idempotency-Key"] = str(idempotency_key)[:256]

    try:
        request = Request(
            "https://api.resend.com/emails", data=payload, headers=headers, method="POST"
        )
        with urlopen(request, timeout=15) as response:
            return 200 <= response.status < 300
    except (HTTPError, URLError, TimeoutError, OSError):
        logger.exception("Resend could not deliver email to %s", to_email)
        return False


def _send_with_smtp(to_email, subject, html_content):
    username = os.environ.get("SMTP_USER") or os.environ.get("EMAIL_USER")
    password = os.environ.get("SMTP_PASSWORD") or os.environ.get("EMAIL_PASS")
    if not username or not password:
        return False

    host = os.environ.get("SMTP_HOST", "smtp.gmail.com")
    port = int(os.environ.get("SMTP_PORT", "587"))
    sender = os.environ.get("EMAIL_FROM") or f"Budget Buddy <{username}>"
    use_tls = os.environ.get("SMTP_USE_TLS", "1").lower() not in {"0", "false", "no"}

    message = EmailMessage()
    message["From"] = sender
    message["To"] = to_email
    message["Subject"] = subject
    message.set_content("Email này cần một ứng dụng hỗ trợ HTML để hiển thị đầy đủ.")
    message.add_alternative(html_content, subtype="html")

    try:
        if port == 465:
            with smtplib.SMTP_SSL(host, port, timeout=15, context=ssl.create_default_context()) as server:
                server.login(username, password)
                server.send_message(message)
        else:
            with smtplib.SMTP(host, port, timeout=15) as server:
                if use_tls:
                    server.starttls(context=ssl.create_default_context())
                server.login(username, password)
                server.send_message(message)
        return True
    except (OSError, smtplib.SMTPException):
        logger.exception("SMTP could not deliver email to %s", to_email)
        return False


def send_email(to_email, subject, html_content, idempotency_key=None):
    """Send through Resend HTTPS on Render, with SMTP as a compatible fallback."""
    if os.environ.get("RESEND_API_KEY") and os.environ.get("EMAIL_FROM"):
        return _send_with_resend(to_email, subject, html_content, idempotency_key)
    return _send_with_smtp(to_email, subject, html_content)
