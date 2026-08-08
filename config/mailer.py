import base64
import hashlib
import json
import logging
import os
import smtplib
import ssl
from email.message import EmailMessage
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from dotenv import load_dotenv


load_dotenv()
logger = logging.getLogger(__name__)

GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GMAIL_SEND_URL = "https://gmail.googleapis.com/gmail/v1/users/me/messages/send"


def _gmail_api_configured():
    return all(
        os.environ.get(name)
        for name in (
            "GMAIL_CLIENT_ID",
            "GMAIL_CLIENT_SECRET",
            "GMAIL_REFRESH_TOKEN",
            "EMAIL_USER",
        )
    )


def email_delivery_configured():
    resend_ready = bool(os.environ.get("RESEND_API_KEY") and os.environ.get("EMAIL_FROM"))
    smtp_user = os.environ.get("SMTP_USER") or os.environ.get("EMAIL_USER")
    smtp_password = os.environ.get("SMTP_PASSWORD") or os.environ.get("EMAIL_PASS")
    return _gmail_api_configured() or resend_ready or bool(smtp_user and smtp_password)


def _clean_header(value):
    return str(value).replace("\r", " ").replace("\n", " ").strip()


def _build_message(to_email, subject, html_content, idempotency_key=None):
    sender_email = os.environ.get("EMAIL_USER") or os.environ.get("SMTP_USER")
    sender = os.environ.get("EMAIL_FROM") or f"Budget Buddy <{sender_email}>"
    message = EmailMessage()
    message["From"] = _clean_header(sender)
    message["To"] = _clean_header(to_email)
    message["Subject"] = _clean_header(subject)
    if idempotency_key:
        digest = hashlib.sha256(str(idempotency_key).encode("utf-8")).hexdigest()
        message["Message-ID"] = f"<{digest}@budget-buddy.local>"
    message.set_content("Email này cần một ứng dụng hỗ trợ HTML để hiển thị đầy đủ.")
    message.add_alternative(html_content, subtype="html")
    return message


def _gmail_access_token():
    payload = urlencode({
        "client_id": os.environ["GMAIL_CLIENT_ID"],
        "client_secret": os.environ["GMAIL_CLIENT_SECRET"],
        "refresh_token": os.environ["GMAIL_REFRESH_TOKEN"],
        "grant_type": "refresh_token",
    }).encode("utf-8")
    request = Request(
        GOOGLE_TOKEN_URL,
        data=payload,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        method="POST",
    )
    with urlopen(request, timeout=15) as response:
        result = json.loads(response.read().decode("utf-8"))
    token = result.get("access_token")
    if not token:
        raise ValueError("Google OAuth response did not contain an access token")
    return token


def _send_with_gmail_api(to_email, subject, html_content, idempotency_key=None):
    if not _gmail_api_configured():
        return False
    try:
        access_token = _gmail_access_token()
        message = _build_message(to_email, subject, html_content, idempotency_key)
        raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode("ascii")
        request = Request(
            GMAIL_SEND_URL,
            data=json.dumps({"raw": raw_message}).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json",
                "User-Agent": "Budget-Buddy/1.0",
            },
            method="POST",
        )
        with urlopen(request, timeout=15) as response:
            return 200 <= response.status < 300
    except HTTPError as error:
        try:
            details = error.read().decode("utf-8", errors="replace")[:1000]
        except OSError:
            details = str(error)
        logger.error(
            "Gmail API HTTP %s while delivering to %s: %s",
            error.code,
            to_email,
            details,
        )
        return False
    except (URLError, TimeoutError, OSError, ValueError, KeyError):
        logger.exception("Gmail API could not deliver email to %s", to_email)
        return False


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


def _send_with_smtp(to_email, subject, html_content, idempotency_key=None):
    username = os.environ.get("SMTP_USER") or os.environ.get("EMAIL_USER")
    password = os.environ.get("SMTP_PASSWORD") or os.environ.get("EMAIL_PASS")
    if not username or not password:
        return False

    host = os.environ.get("SMTP_HOST", "smtp.gmail.com")
    port = int(os.environ.get("SMTP_PORT", "587"))
    use_tls = os.environ.get("SMTP_USE_TLS", "1").lower() not in {"0", "false", "no"}
    message = _build_message(to_email, subject, html_content, idempotency_key)

    try:
        if port == 465:
            with smtplib.SMTP_SSL(
                host, port, timeout=15, context=ssl.create_default_context()
            ) as server:
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
    """Prefer Gmail API HTTPS, then Resend HTTPS, with SMTP as a final fallback."""
    if _gmail_api_configured():
        return _send_with_gmail_api(to_email, subject, html_content, idempotency_key)
    if os.environ.get("RESEND_API_KEY") and os.environ.get("EMAIL_FROM"):
        return _send_with_resend(to_email, subject, html_content, idempotency_key)
    return _send_with_smtp(to_email, subject, html_content, idempotency_key)
