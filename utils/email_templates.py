from html import escape


CATEGORY_VI = {
    "Food & Drinks": "Ăn uống",
    "Transport": "Di chuyển",
    "Education": "Giáo dục",
    "Entertainment": "Giải trí",
    "Shopping": "Mua sắm",
    "Income": "Thu nhập",
    "Other": "Khác",
}


def normalize_preferences(language="en", currency="VND", usd_vnd_rate=25000):
    language = language if language in {"en", "vi"} else "en"
    currency = currency if currency in {"VND", "USD"} else "VND"
    try:
        usd_vnd_rate = float(usd_vnd_rate)
    except (TypeError, ValueError):
        usd_vnd_rate = 25000.0
    return language, currency, usd_vnd_rate if usd_vnd_rate > 0 else 25000.0


def category_label(category, language="en"):
    category = str(category)
    if language == "vi":
        return CATEGORY_VI.get(category, category)
    return {value: key for key, value in CATEGORY_VI.items()}.get(category, category)


def format_money(amount, currency="VND", usd_vnd_rate=25000):
    _, currency, usd_vnd_rate = normalize_preferences("en", currency, usd_vnd_rate)
    amount = float(amount)
    if currency == "USD":
        return f"${amount / usd_vnd_rate:,.2f}"
    return f"{amount:,.0f} ₫".replace(",", ".")


def _email_shell(
    title, username, content, language="en", accent="#0D9488",
    cta_text=None, cta_url=None,
):
    language, _, _ = normalize_preferences(language)
    greeting = "Hello" if language == "en" else "Xin chào"
    footer = (
        "Automated notification from Budget Buddy · Please do not reply"
        if language == "en"
        else "Thông báo tự động từ Budget Buddy · Không trả lời email này"
    )
    cta = ""
    if cta_text and cta_url:
        cta = f"""<div style="text-align:center;margin-top:24px"><a href="{escape(str(cta_url), quote=True)}" style="display:inline-block;background:{accent};color:#fff;text-decoration:none;font-weight:700;padding:12px 22px;border-radius:10px">{escape(str(cta_text))}</a></div>"""
    return f"""<!doctype html>
<html lang="{language}"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width"></head>
<body style="margin:0;background:#F8FAFC;font-family:Arial,sans-serif;color:#334155">
<table width="100%" cellspacing="0" cellpadding="0" style="padding:36px 12px;background:#F8FAFC"><tr><td align="center">
<table width="100%" cellspacing="0" cellpadding="0" style="max-width:560px;background:#fff;border:1px solid #E2E8F0;border-radius:16px;overflow:hidden">
<tr><td style="padding:20px 24px;border-bottom:1px solid #E2E8F0"><b style="font-size:17px">💰 Budget Buddy</b><div style="font-size:12px;color:#64748B;margin-top:3px">· Smart Finance</div></td></tr>
<tr><td style="padding:18px 24px;background:{accent};color:#fff;font-size:19px;font-weight:700">{escape(str(title))}</td></tr>
<tr><td style="padding:24px;font-size:14px;line-height:1.65"><p style="margin-top:0">{greeting} <b>{escape(str(username))}</b>,</p>{content}{cta}</td></tr>
<tr><td style="padding:15px 24px;background:#F8FAFC;border-top:1px solid #E2E8F0;text-align:center;color:#64748B;font-size:12px">{footer}</td></tr>
</table></td></tr></table></body></html>"""


def verification_template(
    username, verification_url, language="en", currency="VND", usd_vnd_rate=25000,
):
    language, _, _ = normalize_preferences(language, currency, usd_vnd_rate)
    if language == "vi":
        title, cta = "Xác minh địa chỉ email", "Xác minh email"
        content = "<p>Cảm ơn bạn đã đăng ký. Hãy xác minh địa chỉ email để kích hoạt tài khoản và bảo vệ dữ liệu tài chính của bạn.</p><p style='font-size:12px;color:#64748B'>Liên kết có hiệu lực trong 24 giờ. Nếu bạn không tạo tài khoản, hãy bỏ qua email này.</p>"
    else:
        title, cta = "Verify your email address", "Verify email"
        content = "<p>Thank you for signing up. Verify your email address to activate your account and protect your financial data.</p><p style='font-size:12px;color:#64748B'>This link is valid for 24 hours. If you did not create this account, you can ignore this email.</p>"
    return _email_shell(title, username, content, language, cta_text=cta, cta_url=verification_url)


def alert_template(
    username, category, spent, limit, alert_type="overbudget", cta_url=None,
    language="en", currency="VND", usd_vnd_rate=25000,
):
    language, currency, usd_vnd_rate = normalize_preferences(language, currency, usd_vnd_rate)
    is_over = alert_type == "overbudget"
    accent = "#DC2626" if is_over else "#D97706"
    category_name = escape(category_label(category, language))
    over = max(0, float(spent) - float(limit or 0))
    if language == "vi":
        title = "⚠️ Cảnh báo vượt ngân sách" if is_over else "🚨 Chi tiêu bất thường"
        intro = f"Danh mục <b>{category_name}</b> vừa vượt hạn mức bạn đã đặt."
        labels, cta = ("Đã chi", "Hạn mức", "Vượt"), "Xem ngân sách"
    else:
        title = "⚠️ Budget limit exceeded" if is_over else "🚨 Unusual spending"
        intro = f"Your <b>{category_name}</b> category has just exceeded its budget limit."
        labels, cta = ("Spent", "Limit", "Over"), "Review budget"
    content = f"""<p>{intro}</p><table width="100%" cellspacing="0" cellpadding="8" style="background:#F8FAFC;border:1px solid #E2E8F0;border-radius:10px">
<tr><td>{labels[0]}</td><td align="right"><b style="color:#DC2626">{format_money(spent, currency, usd_vnd_rate)}</b></td></tr>
<tr><td>{labels[1]}</td><td align="right"><b>{format_money(limit, currency, usd_vnd_rate)}</b></td></tr>
<tr><td>{labels[2]}</td><td align="right"><b style="color:#DC2626">{format_money(over, currency, usd_vnd_rate)}</b></td></tr></table>"""
    return _email_shell(title, username, content, language, accent, cta, cta_url)


def weekly_summary_template(
    username, week_start, week_end, income, expense, previous_expense,
    by_category, transactions, app_url, language="en", currency="VND",
    usd_vnd_rate=25000,
):
    language, currency, usd_vnd_rate = normalize_preferences(language, currency, usd_vnd_rate)
    if previous_expense > 0:
        change = round((expense - previous_expense) / previous_expense * 100)
        if language == "vi":
            comparison = f"{'tăng' if change > 0 else 'giảm' if change < 0 else 'không đổi'} {abs(change)}% so với tuần trước" if change else "bằng tuần trước"
        else:
            comparison = f"{'increased' if change > 0 else 'decreased'} {abs(change)}% from last week" if change else "was unchanged from last week"
    else:
        comparison = "chưa có dữ liệu tuần trước để so sánh" if language == "vi" else "has no previous-week data for comparison"
    empty_cat = "Chưa có khoản chi trong tuần." if language == "vi" else "No spending was recorded this week."
    category_rows = "".join(
        f'<tr><td>{escape(category_label(name, language))}</td><td align="right"><b>{format_money(amount, currency, usd_vnd_rate)}</b></td></tr>'
        for name, amount in sorted(by_category.items(), key=lambda item: item[1], reverse=True)[:6]
    ) or f'<tr><td colspan="2" style="color:#64748B">{empty_cat}</td></tr>'
    empty_tx = "Không có giao dịch chi tiêu." if language == "vi" else "No expense transactions were recorded."
    transaction_rows = "".join(
        f'<tr><td>{escape(str(tx.get("date", "")))}</td><td>{escape(str(tx.get("merchant", "")))}</td><td align="right" style="color:#DC2626"><b>-{format_money(abs(tx.get("amount", 0)), currency, usd_vnd_rate)}</b></td></tr>'
        for tx in transactions[:8] if tx.get("amount", 0) < 0
    ) or f'<tr><td colspan="3" style="color:#64748B">{empty_tx}</td></tr>'
    if language == "vi":
        intro = f"Đây là tổng kết từ <b>{escape(str(week_start))}</b> đến <b>{escape(str(week_end))}</b>."
        labels = ("Thu nhập", "Chi tiêu", "Chênh lệch")
        compare = f"<b>So sánh:</b> Chi tiêu {escape(comparison)}."
        headings = ("Chi theo danh mục", "Giao dịch chi tiêu gần nhất")
        title, cta = "📊 Báo cáo chi tiêu hàng tuần", "Mở Budget Buddy"
    else:
        intro = f"Here is your summary from <b>{escape(str(week_start))}</b> to <b>{escape(str(week_end))}</b>."
        labels = ("Income", "Spending", "Net")
        compare = f"<b>Comparison:</b> Spending {escape(comparison)}."
        headings = ("Spending by category", "Recent expense transactions")
        title, cta = "📊 Weekly spending report", "Open Budget Buddy"
    content = f"""<p>{intro}</p><table width="100%" cellspacing="0" cellpadding="9" style="background:#F8FAFC;border:1px solid #E2E8F0;border-radius:10px;margin-bottom:18px">
<tr><td>{labels[0]}</td><td align="right"><b style="color:#059669">+{format_money(income, currency, usd_vnd_rate)}</b></td></tr>
<tr><td>{labels[1]}</td><td align="right"><b style="color:#DC2626">-{format_money(expense, currency, usd_vnd_rate)}</b></td></tr>
<tr><td>{labels[2]}</td><td align="right"><b>{format_money(income-expense, currency, usd_vnd_rate)}</b></td></tr></table>
<p style="background:#ECFDF5;padding:10px 12px;border-radius:8px">{compare}</p><h3 style="font-size:15px;margin-top:22px">{headings[0]}</h3>
<table width="100%" cellspacing="0" cellpadding="7" style="border-collapse:collapse">{category_rows}</table><h3 style="font-size:15px;margin-top:22px">{headings[1]}</h3>
<table width="100%" cellspacing="0" cellpadding="7" style="border-collapse:collapse">{transaction_rows}</table>"""
    return _email_shell(title, username, content, language, cta_text=cta, cta_url=app_url)


def forecast_template(
    username, income, expected_expense, predicted_balance, app_url=None,
    language="en", currency="VND", usd_vnd_rate=25000,
):
    language, currency, usd_vnd_rate = normalize_preferences(language, currency, usd_vnd_rate)
    if language == "vi":
        intro, labels, title, cta = "Dự báo dòng tiền cuối tháng dựa trên dữ liệu hiện tại:", ("Thu nhập", "Chi dự kiến", "Số dư dự kiến"), "Dự báo dòng tiền", "Xem tổng quan"
    else:
        intro, labels, title, cta = "Month-end cash-flow forecast based on current data:", ("Income", "Expected spending", "Projected balance"), "Cash-flow forecast", "View overview"
    content = f"""<p>{intro}</p><table width="100%" cellspacing="0" cellpadding="8" style="background:#F8FAFC;border:1px solid #E2E8F0;border-radius:10px">
<tr><td>{labels[0]}</td><td align="right"><b style="color:#059669">+{format_money(income, currency, usd_vnd_rate)}</b></td></tr>
<tr><td>{labels[1]}</td><td align="right"><b style="color:#DC2626">-{format_money(expected_expense, currency, usd_vnd_rate)}</b></td></tr>
<tr><td>{labels[2]}</td><td align="right"><b>{format_money(predicted_balance, currency, usd_vnd_rate)}</b></td></tr></table>"""
    return _email_shell(title, username, content, language, cta_text=cta, cta_url=app_url)


def goal_plan_template(
    username, goal_name, target, current_saved, monthly_needed, est_months,
    app_url=None, language="en", currency="VND", usd_vnd_rate=25000,
):
    language, currency, usd_vnd_rate = normalize_preferences(language, currency, usd_vnd_rate)
    pct = min(100, round(float(current_saved) / float(target) * 100)) if target else 0
    if language == "vi":
        intro, labels, duration = f"Cập nhật mục tiêu <b>{escape(str(goal_name))}</b>:", ("Tiến độ", "Đã tích lũy", "Đề xuất mỗi tháng", "Thời gian ước tính"), f"{int(est_months)} tháng"
        title, cta = "🎯 Kế hoạch mục tiêu", "Xem mục tiêu"
    else:
        intro, labels, duration = f"Update for your <b>{escape(str(goal_name))}</b> goal:", ("Progress", "Saved", "Suggested monthly amount", "Estimated time"), f"{int(est_months)} months"
        title, cta = "🎯 Goal plan", "View goals"
    content = f"""<p>{intro}</p><table width="100%" cellspacing="0" cellpadding="8" style="background:#F8FAFC;border:1px solid #E2E8F0;border-radius:10px">
<tr><td>{labels[0]}</td><td align="right"><b>{pct}%</b></td></tr><tr><td>{labels[1]}</td><td align="right"><b>{format_money(current_saved, currency, usd_vnd_rate)} / {format_money(target, currency, usd_vnd_rate)}</b></td></tr>
<tr><td>{labels[2]}</td><td align="right"><b>{format_money(monthly_needed, currency, usd_vnd_rate)}</b></td></tr><tr><td>{labels[3]}</td><td align="right"><b>{duration}</b></td></tr></table>"""
    return _email_shell(title, username, content, language, "#7C3AED", cta, f"{app_url}/goals" if app_url else None)
