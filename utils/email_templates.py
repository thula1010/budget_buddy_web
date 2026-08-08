from html import escape


def format_vnd(amount):
    return f"{float(amount):,.0f} ₫".replace(",", ".")


def _email_shell(title, username, content, accent="#0D9488", cta_text=None, cta_url=None):
    safe_title = escape(str(title))
    safe_username = escape(str(username))
    cta = ""
    if cta_text and cta_url:
        cta = f"""
        <div style="text-align:center;margin-top:24px">
          <a href="{escape(str(cta_url), quote=True)}" style="display:inline-block;background:{accent};color:#fff;text-decoration:none;font-weight:700;padding:12px 22px;border-radius:10px">{escape(str(cta_text))}</a>
        </div>"""
    return f"""<!doctype html>
<html lang="vi"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width"></head>
<body style="margin:0;background:#F8FAFC;font-family:Arial,sans-serif;color:#334155">
  <table width="100%" cellspacing="0" cellpadding="0" style="padding:36px 12px;background:#F8FAFC"><tr><td align="center">
    <table width="100%" cellspacing="0" cellpadding="0" style="max-width:560px;background:#fff;border:1px solid #E2E8F0;border-radius:16px;overflow:hidden">
      <tr><td style="padding:20px 24px;border-bottom:1px solid #E2E8F0"><b style="font-size:17px">💰 Budget Buddy</b><div style="font-size:12px;color:#64748B;margin-top:3px">· Smart Finance</div></td></tr>
      <tr><td style="padding:18px 24px;background:{accent};color:#fff;font-size:19px;font-weight:700">{safe_title}</td></tr>
      <tr><td style="padding:24px;font-size:14px;line-height:1.65"><p style="margin-top:0">Xin chào <b>{safe_username}</b>,</p>{content}{cta}</td></tr>
      <tr><td style="padding:15px 24px;background:#F8FAFC;border-top:1px solid #E2E8F0;text-align:center;color:#64748B;font-size:12px">Thông báo tự động từ Budget Buddy · Không trả lời email này</td></tr>
    </table>
  </td></tr></table>
</body></html>"""


def verification_template(username, verification_url):
    content = """
      <p>Cảm ơn bạn đã đăng ký. Hãy xác minh địa chỉ email để kích hoạt tài khoản và bảo vệ dữ liệu tài chính của bạn.</p>
      <p style="font-size:12px;color:#64748B">Liên kết có hiệu lực trong 24 giờ. Nếu bạn không tạo tài khoản, hãy bỏ qua email này.</p>
    """
    return _email_shell(
        "Xác minh địa chỉ email",
        username,
        content,
        cta_text="Xác minh email",
        cta_url=verification_url,
    )


def alert_template(
    username, category, spent, limit, alert_type="overbudget", cta_url=None
):
    is_over = alert_type == "overbudget"
    title = "⚠️ Cảnh báo vượt ngân sách" if is_over else "🚨 Chi tiêu bất thường"
    accent = "#DC2626" if is_over else "#D97706"
    category_name = escape(str(category))
    over = max(0, float(spent) - float(limit or 0))
    detail = f"""
      <p>Danh mục <b>{category_name}</b> vừa vượt hạn mức bạn đã đặt.</p>
      <table width="100%" cellspacing="0" cellpadding="8" style="background:#F8FAFC;border:1px solid #E2E8F0;border-radius:10px">
        <tr><td>Đã chi</td><td align="right"><b style="color:#DC2626">{format_vnd(spent)}</b></td></tr>
        <tr><td>Hạn mức</td><td align="right"><b>{format_vnd(limit)}</b></td></tr>
        <tr><td>Vượt</td><td align="right"><b style="color:#DC2626">{format_vnd(over)}</b></td></tr>
      </table>
    """
    return _email_shell(
        title,
        username,
        detail,
        accent=accent,
        cta_text="Xem ngân sách",
        cta_url=cta_url,
    )


def weekly_summary_template(
    username,
    week_start,
    week_end,
    income,
    expense,
    previous_expense,
    by_category,
    transactions,
    app_url,
):
    if previous_expense > 0:
        change = round((expense - previous_expense) / previous_expense * 100)
        comparison = (
            f"tăng {abs(change)}% so với tuần trước"
            if change > 0
            else f"giảm {abs(change)}% so với tuần trước"
            if change < 0
            else "bằng tuần trước"
        )
    else:
        comparison = "chưa có dữ liệu tuần trước để so sánh"

    category_rows = "".join(
        f'<tr><td>{escape(str(name))}</td><td align="right"><b>{format_vnd(amount)}</b></td></tr>'
        for name, amount in sorted(by_category.items(), key=lambda item: item[1], reverse=True)[:6]
    ) or '<tr><td colspan="2" style="color:#64748B">Chưa có khoản chi trong tuần.</td></tr>'

    transaction_rows = "".join(
        f'<tr><td>{escape(str(tx.get("date", "")))}</td><td>{escape(str(tx.get("merchant", "")))}</td><td align="right" style="color:#DC2626"><b>-{format_vnd(abs(tx.get("amount", 0)))}</b></td></tr>'
        for tx in transactions[:8]
        if tx.get("amount", 0) < 0
    ) or '<tr><td colspan="3" style="color:#64748B">Không có giao dịch chi tiêu.</td></tr>'

    content = f"""
      <p>Đây là tổng kết từ <b>{escape(str(week_start))}</b> đến <b>{escape(str(week_end))}</b>.</p>
      <table width="100%" cellspacing="0" cellpadding="9" style="background:#F8FAFC;border:1px solid #E2E8F0;border-radius:10px;margin-bottom:18px">
        <tr><td>Thu nhập</td><td align="right"><b style="color:#059669">+{format_vnd(income)}</b></td></tr>
        <tr><td>Chi tiêu</td><td align="right"><b style="color:#DC2626">-{format_vnd(expense)}</b></td></tr>
        <tr><td>Chênh lệch</td><td align="right"><b>{format_vnd(income-expense)}</b></td></tr>
      </table>
      <p style="background:#ECFDF5;padding:10px 12px;border-radius:8px"><b>So sánh:</b> Chi tiêu {escape(comparison)}.</p>
      <h3 style="font-size:15px;margin-top:22px">Chi theo danh mục</h3>
      <table width="100%" cellspacing="0" cellpadding="7" style="border-collapse:collapse">{category_rows}</table>
      <h3 style="font-size:15px;margin-top:22px">Giao dịch chi tiêu gần nhất</h3>
      <table width="100%" cellspacing="0" cellpadding="7" style="border-collapse:collapse">{transaction_rows}</table>
    """
    return _email_shell(
        "📊 Báo cáo chi tiêu hàng tuần",
        username,
        content,
        cta_text="Mở Budget Buddy",
        cta_url=app_url,
    )


def forecast_template(username, income, expected_expense, predicted_balance, app_url=None):
    content = f"""
      <p>Dự báo dòng tiền cuối tháng dựa trên dữ liệu hiện tại:</p>
      <table width="100%" cellspacing="0" cellpadding="8" style="background:#F8FAFC;border:1px solid #E2E8F0;border-radius:10px">
        <tr><td>Thu nhập</td><td align="right"><b style="color:#059669">+{format_vnd(income)}</b></td></tr>
        <tr><td>Chi dự kiến</td><td align="right"><b style="color:#DC2626">-{format_vnd(expected_expense)}</b></td></tr>
        <tr><td>Số dư dự kiến</td><td align="right"><b>{format_vnd(predicted_balance)}</b></td></tr>
      </table>
    """
    return _email_shell("Dự báo dòng tiền", username, content, cta_text="Xem tổng quan", cta_url=app_url)


def goal_plan_template(
    username, goal_name, target, current_saved, monthly_needed, est_months, app_url=None
):
    pct = min(100, round(float(current_saved) / float(target) * 100)) if target else 0
    content = f"""
      <p>Cập nhật mục tiêu <b>{escape(str(goal_name))}</b>:</p>
      <table width="100%" cellspacing="0" cellpadding="8" style="background:#F8FAFC;border:1px solid #E2E8F0;border-radius:10px">
        <tr><td>Tiến độ</td><td align="right"><b>{pct}%</b></td></tr>
        <tr><td>Đã tích lũy</td><td align="right"><b>{format_vnd(current_saved)} / {format_vnd(target)}</b></td></tr>
        <tr><td>Đề xuất mỗi tháng</td><td align="right"><b>{format_vnd(monthly_needed)}</b></td></tr>
        <tr><td>Thời gian ước tính</td><td align="right"><b>{int(est_months)} tháng</b></td></tr>
      </table>
    """
    return _email_shell("🎯 Kế hoạch mục tiêu", username, content, accent="#7C3AED", cta_text="Xem mục tiêu", cta_url=f"{app_url}/goals" if app_url else None)
