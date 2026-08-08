"""Gửi thử email cảnh báo bằng cấu hình Resend/SMTP hiện tại."""

import os

from config.mailer import email_delivery_configured
from services.notification import send_budget_alert_email


receiver = os.environ.get("TEST_EMAIL_RECEIVER")
if not receiver:
    raise SystemExit("Hãy đặt TEST_EMAIL_RECEIVER=dia-chi-email-cua-ban trước khi chạy.")
if not email_delivery_configured():
    raise SystemExit("Chưa cấu hình Resend hoặc SMTP trong file .env.")

print("Đang gửi email cảnh báo ngân sách thử nghiệm...")
success = send_budget_alert_email(
    to_email=receiver,
    username="Người dùng thử nghiệm",
    category="Ăn uống",
    spent=1_500_000,
    limit=1_000_000,
    alert_type="overbudget",
    idempotency_key="manual-budget-alert-test",
)
print("Gửi thành công. Hãy kiểm tra hộp thư." if success else "Gửi thất bại. Hãy kiểm tra cấu hình email.")
