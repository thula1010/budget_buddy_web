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


def send_verification_email(to_email, username, verification_url):
    return send_email(
        to_email,
        "[Budget Buddy] Xác minh địa chỉ email",
        verification_template(username, verification_url),
        idempotency_key=f"verify-{to_email}-{verification_url[-20:]}",
    )


def send_budget_alert_email(
    to_email, username, category, spent, limit, alert_type="overbudget", idempotency_key=None
):
    subject = (
        f"[Cảnh báo] Vượt ngân sách {category}"
        if alert_type == "overbudget"
        else f"[Cảnh báo] Chi tiêu bất thường {category}"
    )
    html = alert_template(
        username, category, spent, limit, alert_type, f"{app_base_url()}/budgets"
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
):
    subject = f"[Báo cáo tuần] Chi tiêu {week_start} - {week_end}"
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
    )
    return send_email(to_email, subject, html, idempotency_key=idempotency_key)


def send_forecast_email(to_email, username, income, expected_expense, predicted_balance):
    subject = "[Báo cáo] Dự báo dòng tiền cuối tháng"
    html = forecast_template(
        username, income, expected_expense, predicted_balance, app_base_url()
    )
    return send_email(to_email, subject, html)


def send_goal_plan_email(
    to_email, username, goal_name, target, current_saved, monthly_needed, est_months
):
    subject = f"[Mục tiêu] Kế hoạch tích lũy {goal_name}"
    html = goal_plan_template(
        username,
        goal_name,
        target,
        current_saved,
        monthly_needed,
        est_months,
        app_base_url(),
    )
    return send_email(to_email, subject, html)
