import os

from config.mailer import email_delivery_configured, send_email
from utils.email_templates import (
    alert_template,
    forecast_template,
    goal_plan_template,
    verification_template,
    weekly_summary_template,
)


def app_base_url():
    return os.environ.get("APP_BASE_URL", "http://127.0.0.1:5000").rstrip("/")


def send_verification_email(
    to_email, username, verification_url, language="en", currency="VND",
    usd_vnd_rate=25000,
):
    subject = (
        "[Budget Buddy] Xác minh địa chỉ email"
        if language == "vi"
        else "[Budget Buddy] Verify your email address"
    )
    return send_email(
        to_email,
        subject,
        verification_template(
            username, verification_url, language, currency, usd_vnd_rate
        ),
        idempotency_key=f"verify-{to_email}-{verification_url[-20:]}",
    )


def send_budget_alert_email(
    to_email, username, category, spent, limit, alert_type="overbudget",
    idempotency_key=None, language="en", currency="VND", usd_vnd_rate=25000,
):
    if language == "vi":
        subject = f"[Cảnh báo] {'Vượt ngân sách' if alert_type == 'overbudget' else 'Chi tiêu bất thường'} {category}"
    else:
        subject = f"[Alert] {'Budget exceeded' if alert_type == 'overbudget' else 'Unusual spending'}: {category}"
    html = alert_template(
        username, category, spent, limit, alert_type, f"{app_base_url()}/budgets",
        language, currency, usd_vnd_rate,
    )
    return send_email(to_email, subject, html, idempotency_key=idempotency_key)


def send_weekly_summary_email(
    to_email,
    username,
    week_start,
    week_end,
    income,
    expense,
    previous_expense,
    by_category,
    transactions,
    idempotency_key=None,
    language="en",
    currency="VND",
    usd_vnd_rate=25000,
):
    subject = (
        f"[Báo cáo tuần] Chi tiêu {week_start} - {week_end}"
        if language == "vi"
        else f"[Weekly report] Spending {week_start} - {week_end}"
    )
    html = weekly_summary_template(
        username,
        week_start,
        week_end,
        income,
        expense,
        previous_expense,
        by_category,
        transactions,
        app_base_url(),
        language,
        currency,
        usd_vnd_rate,
    )
    return send_email(to_email, subject, html, idempotency_key=idempotency_key)


def send_forecast_email(
    to_email, username, income, expected_expense, predicted_balance,
    language="en", currency="VND", usd_vnd_rate=25000,
):
    subject = "[Báo cáo] Dự báo dòng tiền cuối tháng" if language == "vi" else "[Report] Month-end cash-flow forecast"
    html = forecast_template(
        username, income, expected_expense, predicted_balance, app_base_url(),
        language, currency, usd_vnd_rate,
    )
    return send_email(to_email, subject, html)


def send_goal_plan_email(
    to_email, username, goal_name, target, current_saved, monthly_needed, est_months,
    language="en", currency="VND", usd_vnd_rate=25000,
):
    subject = f"[Mục tiêu] Kế hoạch tích lũy {goal_name}" if language == "vi" else f"[Goal] Savings plan: {goal_name}"
    html = goal_plan_template(
        username,
        goal_name,
        target,
        current_saved,
        monthly_needed,
        est_months,
        app_base_url(),
        language,
        currency,
        usd_vnd_rate,
    )
    return send_email(to_email, subject, html)
