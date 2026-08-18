import base64
import hashlib
import json
import math
import os
import re
from datetime import UTC, date, datetime, timedelta
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

import click
from flask import Flask, flash, jsonify, redirect, render_template, request, url_for
from flask_login import LoginManager, UserMixin, current_user, login_required, login_user, logout_user
from flask_sqlalchemy import SQLAlchemy
from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer
from sqlalchemy import inspect, text
from dotenv import load_dotenv
from werkzeug.security import check_password_hash, generate_password_hash

try:
    from openai import OpenAI
except ImportError:  # AI features remain optional until dependencies are installed.
    OpenAI = None

try:
    from config.mailer import email_delivery_configured
    from services.notification import (
        send_budget_alert_email,
        send_goal_plan_email,
        send_verification_email,
        send_weekly_summary_email,
    )
except Exception:
    email_delivery_configured = lambda: False
    send_budget_alert_email = None
    send_goal_plan_email = None
    send_verification_email = None
    send_weekly_summary_email = None


load_dotenv()
app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-only-change-me")
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get(
    "DATABASE_URL", f"sqlite:///{os.path.join(app.instance_path, 'app.db')}"
)
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["MAX_CONTENT_LENGTH"] = 8 * 1024 * 1024
app.config["EMAIL_VERIFICATION_REQUIRED"] = os.environ.get(
    "EMAIL_VERIFICATION_REQUIRED", "1"
).lower() not in {"0", "false", "no"}
app.config["EMAIL_VERIFICATION_MAX_AGE"] = int(
    os.environ.get("EMAIL_VERIFICATION_MAX_AGE", str(24 * 60 * 60))
)
os.makedirs(app.instance_path, exist_ok=True)

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = "login"


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    email_verified = db.Column(db.Boolean, nullable=False, default=False)
    email_verified_at = db.Column(db.DateTime, nullable=True)
    verification_sent_at = db.Column(db.DateTime, nullable=True)
    weekly_email_enabled = db.Column(db.Boolean, nullable=False, default=True)
    budget_alerts_enabled = db.Column(db.Boolean, nullable=False, default=True)
    last_weekly_email_at = db.Column(db.DateTime, nullable=True)


class Account(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False, index=True)
    name = db.Column(db.String(100), nullable=False)
    type = db.Column(db.String(30), nullable=False)
    icon = db.Column(db.String(10), nullable=False)
    opening_balance = db.Column(db.Float, nullable=False, default=0)
    __table_args__ = (db.UniqueConstraint("user_id", "name"),)


class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    kind = db.Column(db.String(20), nullable=False)
    icon = db.Column(db.String(10), nullable=False)
    color = db.Column(db.String(10), nullable=False)
    bg = db.Column(db.String(10), nullable=False)


class Transaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False, index=True)
    account_id = db.Column(db.Integer, db.ForeignKey("account.id"), nullable=False, index=True)
    category_id = db.Column(db.Integer, db.ForeignKey("category.id"), nullable=False, index=True)
    amount = db.Column(db.Float, nullable=False)  # Income is positive, expense is negative.
    merchant = db.Column(db.String(200), nullable=False)
    date = db.Column(db.String(10), nullable=False, index=True)
    ai_tagged = db.Column(db.Boolean, nullable=False, default=False)
    created_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(UTC))


class Budget(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False, index=True)
    category_id = db.Column(db.Integer, db.ForeignKey("category.id"), nullable=False)
    limit_vnd = db.Column(db.Float, nullable=False)
    __table_args__ = (db.UniqueConstraint("user_id", "category_id"),)


class Goal(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False, index=True)
    name = db.Column(db.String(100), nullable=False)
    target = db.Column(db.Float, nullable=False)
    current_saved = db.Column(db.Float, nullable=False, default=0)
    deadline = db.Column(db.String(30), nullable=False, default="")
    icon = db.Column(db.String(10), nullable=False, default="🎯")
    accent = db.Column(db.String(10), nullable=False, default="#0D9488")


CATEGORY_SEED = [
    ("Food & Drinks", "expense", "🍜", "#B45309", "#FEF3C7"),
    ("Transport", "expense", "🛵", "#6D28D9", "#EDE9FE"),
    ("Education", "expense", "📚", "#1D4ED8", "#DBEAFE"),
    ("Entertainment", "expense", "🎬", "#BE185D", "#FCE7F3"),
    ("Shopping", "expense", "🛍", "#0F766E", "#CCFBF1"),
    ("Income", "income", "💼", "#047857", "#D1FAE5"),
]
ACCOUNT_SEED = [
    ("Personal Wallet", "cash", "💵", 520000),
    ("MB Bank", "bank", "🏦", 1450000),
    ("Techcombank", "bank", "🏦", 480000),
    ("MoMo", "ewallet", "📱", 260000),
    ("ShopeePay", "ewallet", "📱", 90000),
]
BUDGET_SEED = {
    "Food & Drinks": 600000,
    "Transport": 150000,
    "Entertainment": 80000,
    "Education": 300000,
    "Shopping": 100000,
}


def seed_categories():
    for name, kind, icon, color, bg in CATEGORY_SEED:
        if not Category.query.filter_by(name=name).first():
            db.session.add(Category(name=name, kind=kind, icon=icon, color=color, bg=bg))
    db.session.commit()


def upgrade_user_schema():
    """Add notification fields without invalidating accounts created before this release."""
    schema = inspect(db.engine)
    if "user" not in schema.get_table_names():
        return
    existing = {column["name"] for column in schema.get_columns("user")}
    additions = {
        "email_verified": "BOOLEAN NOT NULL DEFAULT TRUE",
        "email_verified_at": "TIMESTAMP NULL",
        "verification_sent_at": "TIMESTAMP NULL",
        "weekly_email_enabled": "BOOLEAN NOT NULL DEFAULT TRUE",
        "budget_alerts_enabled": "BOOLEAN NOT NULL DEFAULT TRUE",
        "last_weekly_email_at": "TIMESTAMP NULL",
    }
    with db.engine.begin() as connection:
        for column, definition in additions.items():
            if column not in existing:
                connection.exec_driver_sql(
                    f'ALTER TABLE "user" ADD COLUMN "{column}" {definition}'
                )


def prepare_legacy_tables():
    """Rename incompatible pre-fix tables so create_all can build the new schema."""
    table_requirements = {
        "transaction": {"user_id", "account_id", "category_id", "merchant", "ai_tagged", "created_at"},
        "goal": {"user_id", "deadline", "icon", "accent"},
    }
    renamed = []
    schema = inspect(db.engine)
    existing = set(schema.get_table_names())
    with db.engine.begin() as connection:
        for table_name, required_columns in table_requirements.items():
            legacy_name = f"{table_name}_legacy"
            if table_name not in existing or legacy_name in existing:
                continue
            columns = {column["name"] for column in schema.get_columns(table_name)}
            if not required_columns.issubset(columns):
                connection.exec_driver_sql(
                    f'ALTER TABLE "{table_name}" RENAME TO "{legacy_name}"'
                )
                renamed.append(legacy_name)
    return renamed


def migrate_legacy_data(legacy_tables):
    """Import data from the original schema once, then remove only the temp tables."""
    if not legacy_tables:
        return
    users = User.query.order_by(User.id).all()
    if not users:
        app.logger.warning("Legacy finance data exists but there is no user to own it yet.")
        return
    for user in users:
        ensure_user_data(user)
    users_by_id = {user.id: user for user in users}
    fallback_user = users[0]
    categories = Category.query.all()
    categories_by_id = {category.id: category for category in categories}
    categories_by_name = {category.name.lower(): category for category in categories}

    try:
        if "transaction_legacy" in legacy_tables and Transaction.query.count() == 0:
            rows = db.session.execute(text('SELECT * FROM "transaction_legacy"')).mappings().all()
            for row in rows:
                user = users_by_id.get(row.get("user_id")) or fallback_user
                account = None
                if row.get("account_id"):
                    account = Account.query.filter_by(id=row["account_id"], user_id=user.id).first()
                if not account and row.get("account"):
                    account = Account.query.filter_by(user_id=user.id, name=row["account"]).first()
                account = account or Account.query.filter_by(user_id=user.id).order_by(Account.id).first()

                category = categories_by_id.get(row.get("category_id"))
                if not category and row.get("category"):
                    category = categories_by_name.get(str(row["category"]).lower())
                tx_type = row.get("type") or ("income" if float(row.get("amount") or 0) > 0 else "expense")
                category = category or next(
                    c for c in categories if c.kind == ("income" if tx_type == "income" else "expense")
                )
                amount = abs(float(row.get("amount") or 0))
                if amount <= 0:
                    continue
                tx_date = str(row.get("date") or date.today().isoformat())[:10]
                try:
                    datetime.strptime(tx_date, "%Y-%m-%d")
                except ValueError:
                    tx_date = date.today().isoformat()
                db.session.add(Transaction(
                    user_id=user.id,
                    account_id=account.id,
                    category_id=category.id,
                    amount=amount if tx_type == "income" else -amount,
                    merchant=str(row.get("merchant") or row.get("note") or "Giao dịch cũ")[:200],
                    date=tx_date,
                    ai_tagged=bool(row.get("ai_tagged", False)),
                ))

        if "goal_legacy" in legacy_tables and Goal.query.count() == 0:
            rows = db.session.execute(text('SELECT * FROM "goal_legacy"')).mappings().all()
            for row in rows:
                user = users_by_id.get(row.get("user_id")) or fallback_user
                target = float(row.get("target") or 0)
                if target <= 0:
                    continue
                db.session.add(Goal(
                    user_id=user.id,
                    name=str(row.get("name") or "Mục tiêu cũ")[:100],
                    target=target,
                    current_saved=float(row.get("current_saved") or row.get("saved") or 0),
                    deadline=str(row.get("deadline") or "")[:30],
                    icon=str(row.get("icon") or "🎯")[:10],
                    accent=str(row.get("accent") or "#0D9488")[:10],
                ))
        db.session.commit()
        with db.engine.begin() as connection:
            for table_name in legacy_tables:
                connection.exec_driver_sql(f'DROP TABLE IF EXISTS "{table_name}"')
    except Exception:
        db.session.rollback()
        app.logger.exception("Legacy database migration failed; legacy tables were preserved")
        raise


def ensure_user_data(user):
    if not Account.query.filter_by(user_id=user.id).first():
        for name, account_type, icon, balance in ACCOUNT_SEED:
            db.session.add(Account(
                user_id=user.id, name=name, type=account_type, icon=icon,
                opening_balance=balance,
            ))
    if not Budget.query.filter_by(user_id=user.id).first():
        categories = {c.name: c for c in Category.query.all()}
        for name, limit in BUDGET_SEED.items():
            db.session.add(Budget(
                user_id=user.id, category_id=categories[name].id, limit_vnd=limit,
            ))
    db.session.commit()


@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))


def utc_now_naive():
    return datetime.now(UTC).replace(tzinfo=None)


def verification_serializer():
    return URLSafeTimedSerializer(app.config["SECRET_KEY"])


def create_verification_token(user):
    return verification_serializer().dumps(
        {"user_id": user.id, "email": user.email}, salt="email-verification"
    )


def verification_link(user):
    base_url = os.environ.get("APP_BASE_URL") or request.url_root.rstrip("/")
    return f'{base_url.rstrip("/")}{url_for("verify_email", token=create_verification_token(user))}'


def deliver_verification_email(user):
    if not send_verification_email or not email_delivery_configured():
        return False
    delivered = send_verification_email(user.email, user.username, verification_link(user))
    if delivered:
        user.verification_sent_at = utc_now_naive()
        db.session.commit()
    return delivered


def valid_period(value):
    if value and re.fullmatch(r"\d{4}-(0[1-9]|1[0-2])", value):
        return value
    return date.today().strftime("%Y-%m")


def account_transaction_delta(account):
    return float(
        db.session.query(db.func.coalesce(db.func.sum(Transaction.amount), 0))
        .filter_by(user_id=account.user_id, account_id=account.id)
        .scalar()
    )


def account_balance(account):
    return float(account.opening_balance + account_transaction_delta(account))


def serialize_transaction(tx):
    account = db.session.get(Account, tx.account_id)
    category = db.session.get(Category, tx.category_id)
    return {
        "id": tx.id,
        "merchant": tx.merchant,
        "note": tx.merchant,
        "amount": float(tx.amount),
        "type": "income" if tx.amount > 0 else "expense",
        "date": tx.date,
        "category_id": category.id,
        "category": category.name,
        "cat_icon": category.icon,
        "color": category.color,
        "bg": category.bg,
        "account_id": account.id,
        "account": account.name,
        "acc_icon": account.icon,
        "ai_tagged": int(tx.ai_tagged),
        "created_at": tx.created_at.isoformat(timespec="seconds"),
    }


def build_state(user, period=None):
    ensure_user_data(user)
    period = valid_period(period)
    accounts = Account.query.filter_by(user_id=user.id).order_by(Account.id).all()
    categories = Category.query.order_by(Category.id).all()
    transactions = (
        Transaction.query.filter_by(user_id=user.id)
        .order_by(Transaction.date.desc(), Transaction.id.desc())
        .all()
    )
    month_transactions = [t for t in transactions if t.date.startswith(period)]
    income = sum(t.amount for t in month_transactions if t.amount > 0)
    expense = -sum(t.amount for t in month_transactions if t.amount < 0)

    category_by_id = {c.id: c for c in categories}
    budgets = []
    for budget in Budget.query.filter_by(user_id=user.id).order_by(Budget.id).all():
        category = category_by_id[budget.category_id]
        spent = -sum(
            t.amount for t in month_transactions
            if t.category_id == category.id and t.amount < 0
        )
        pct = round(spent / budget.limit_vnd * 100) if budget.limit_vnd else 0
        budgets.append({
            "id": budget.id,
            "category_id": category.id,
            "category": category.name,
            "icon": category.icon,
            "color": category.color,
            "bg": category.bg,
            "limit_vnd": float(budget.limit_vnd),
            "spent": float(spent),
            "pct": pct,
            "over": float(max(0, spent - budget.limit_vnd)),
            "period": period,
        })

    weekly = [0.0, 0.0, 0.0, 0.0]
    by_category = {}
    for tx in month_transactions:
        if tx.amount >= 0:
            continue
        day = int(tx.date[-2:])
        weekly[min((day - 1) // 7, 3)] += -tx.amount
        name = category_by_id[tx.category_id].name
        by_category[name] = by_category.get(name, 0) - tx.amount

    goals = [
        {
            "id": g.id, "name": g.name, "target": float(g.target),
            "saved": float(g.current_saved), "current_saved": float(g.current_saved),
            "icon": g.icon, "accent": g.accent, "deadline": g.deadline,
        }
        for g in Goal.query.filter_by(user_id=user.id).order_by(Goal.id).all()
    ]
    total_balance = sum(account_balance(a) for a in accounts)
    savings_rate = round((income - expense) / income * 100) if income else 0

    notifications = []
    over_budget = sorted((b for b in budgets if b["over"] > 0), key=lambda b: b["over"], reverse=True)
    if over_budget:
        b = over_budget[0]
        notifications.append({
            "id": 1, "kind": "warn", "ago": "Hiện tại",
            "text": f'{b["category"]} đã vượt ngân sách {b["over"]:,.0f} ₫',
        })
    if transactions:
        notifications.append({
            "id": 2, "kind": "done", "ago": "Mới nhất",
            "text": f'Đã đồng bộ giao dịch “{transactions[0].merchant}”',
        })

    return {
        "period": period,
        "user": {
            "name": user.username,
            "initials": user.username[:2].upper(),
            "plan": "Student",
        },
        "accounts": [
            {
                "id": a.id, "name": a.name, "type": a.type, "icon": a.icon,
                "balance": account_balance(a),
            }
            for a in accounts
        ],
        "categories": [
            {
                "id": c.id, "name": c.name, "kind": c.kind, "icon": c.icon,
                "color": c.color, "bg": c.bg,
            }
            for c in categories
        ],
        "transactions": [serialize_transaction(t) for t in transactions],
        "budgets": budgets,
        "goals": goals,
        "notifications": notifications,
        "kpi": {
            "balance": float(total_balance), "income": float(income),
            "expense": float(expense), "savings_rate": savings_rate,
            "target_rate": 70,
        },
        "charts": {"weekly": weekly, "by_category": by_category},
    }


def json_error(message, status=400):
    return jsonify({"error": message}), status


def openai_client():
    if not os.environ.get("OPENAI_API_KEY") or OpenAI is None:
        return None
    return OpenAI()


def extract_json(text):
    text = (text or "").strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*|\s*```$", "", text, flags=re.I)
    return json.loads(text)


def local_coach_reply(message, state):
    query = message.lower()
    kpi = state["kpi"]
    if any(word in query for word in ("số dư", "so du", "tài khoản", "tai khoan")):
        items = ", ".join(f'{a["name"]}: {a["balance"]:,.0f} ₫' for a in state["accounts"])
        return f'Số dư hiện tại: {items}. Tổng cộng {kpi["balance"]:,.0f} ₫.'
    if any(word in query for word in ("ngân sách", "ngan sach", "vượt", "vuot")):
        worst = max(state["budgets"], key=lambda b: b["pct"], default=None)
        if not worst or not worst["spent"]:
            return "Tháng này chưa có khoản chi nào để đánh giá ngân sách."
        action = "Dừng các khoản không thiết yếu trong nhóm này" if worst["over"] else "Giữ mức chi còn lại dưới hạn mức"
        return f'{worst["category"]} đang ở mức {worst["pct"]}% ngân sách. {action}.'
    if any(word in query for word in ("mục tiêu", "muc tieu", "goal", "tiết kiệm", "tiet kiem")):
        if not state["goals"]:
            return "Bạn chưa có mục tiêu tiết kiệm. Hãy tạo một mục tiêu có số tiền và thời hạn cụ thể."
        goal = min(state["goals"], key=lambda g: max(0, g["target"] - g["saved"]))
        remaining = max(0, goal["target"] - goal["saved"])
        return f'“{goal["name"]}” còn {remaining:,.0f} ₫. Hãy dành một khoản cố định ngay sau mỗi lần nhận thu nhập.'
    if kpi["income"] <= 0:
        return f'Tháng này bạn đã chi {kpi["expense"]:,.0f} ₫ nhưng chưa ghi nhận thu nhập. Hãy thêm thu nhập để AI tính tỷ lệ tiết kiệm chính xác.'
    return (
        f'Tháng này bạn thu {kpi["income"]:,.0f} ₫, chi {kpi["expense"]:,.0f} ₫ '
        f'và tỷ lệ tiết kiệm là {kpi["savings_rate"]}%. Ưu tiên giảm danh mục chi lớn nhất trước.'
    )


@app.route("/login")
def login():
    if current_user.is_authenticated:
        return redirect(url_for("overview"))
    return render_template("login.html")


@app.route("/api/login", methods=["POST"])
def api_login():
    user = User.query.filter_by(username=request.form.get("username", "").strip()).first()
    if not user or not check_password_hash(user.password_hash, request.form.get("password", "")):
        flash("Tên đăng nhập hoặc mật khẩu không chính xác!", "error")
        return redirect(url_for("login"))
    if app.config["EMAIL_VERIFICATION_REQUIRED"] and not user.email_verified:
        flash("Vui lòng xác minh email trước khi đăng nhập.", "error")
        return redirect(url_for("verify_email_pending", email=user.email))
    login_user(user)
    ensure_user_data(user)
    return redirect(url_for("overview"))


@app.route("/api/signup", methods=["POST"])
def api_signup():
    username = request.form.get("username", "").strip()
    email = request.form.get("email", "").strip().lower()
    password = request.form.get("password", "")
    if not username or not email or not password:
        flash("Vui lòng nhập đầy đủ thông tin!", "error")
        return redirect(url_for("login"))
    if not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email):
        flash("Địa chỉ email không hợp lệ!", "error")
        return redirect(url_for("login"))
    if len(password) < 8:
        flash("Mật khẩu phải có ít nhất 8 ký tự!", "error")
        return redirect(url_for("login"))
    if password != request.form.get("confirm_password", ""):
        flash("Mật khẩu nhập lại không khớp!", "error")
        return redirect(url_for("login"))
    if User.query.filter((User.username == username) | (User.email == email)).first():
        flash("Tên đăng nhập hoặc email đã tồn tại!", "error")
        return redirect(url_for("login"))
    verification_required = app.config["EMAIL_VERIFICATION_REQUIRED"]
    user = User(
        username=username,
        email=email,
        password_hash=generate_password_hash(password),
        email_verified=not verification_required,
        email_verified_at=utc_now_naive() if not verification_required else None,
    )
    db.session.add(user)
    db.session.commit()
    ensure_user_data(user)
    if verification_required:
        if deliver_verification_email(user):
            flash("Đã gửi email xác minh. Vui lòng kiểm tra hộp thư của bạn.", "success")
        else:
            flash(
                "Tài khoản đã được tạo nhưng chưa gửi được email xác minh. Hãy thử gửi lại.",
                "error",
            )
        return redirect(url_for("verify_email_pending", email=user.email))
    login_user(user)
    return redirect(url_for("overview"))


@app.route("/verify-email-pending")
def verify_email_pending():
    if current_user.is_authenticated:
        return redirect(url_for("overview"))
    return render_template("verify-email-pending.html", email=request.args.get("email", ""))


@app.route("/api/resend-verification", methods=["POST"])
def resend_verification():
    email = request.form.get("email", "").strip().lower()
    user = User.query.filter_by(email=email).first()
    generic_message = "Nếu email tồn tại và chưa được xác minh, liên kết mới sẽ được gửi."
    if not user or user.email_verified:
        flash(generic_message, "success")
        return redirect(url_for("verify_email_pending", email=email))
    if user.verification_sent_at and utc_now_naive() - user.verification_sent_at < timedelta(seconds=60):
        flash("Vui lòng đợi 60 giây trước khi gửi lại.", "error")
        return redirect(url_for("verify_email_pending", email=email))
    if deliver_verification_email(user):
        flash("Đã gửi lại email xác minh.", "success")
    else:
        flash("Chưa gửi được email. Vui lòng thử lại sau.", "error")
    return redirect(url_for("verify_email_pending", email=email))


@app.route("/verify-email/<token>")
def verify_email(token):
    try:
        payload = verification_serializer().loads(
            token,
            salt="email-verification",
            max_age=app.config["EMAIL_VERIFICATION_MAX_AGE"],
        )
    except SignatureExpired:
        flash("Liên kết xác minh đã hết hạn. Vui lòng yêu cầu liên kết mới.", "error")
        return redirect(url_for("verify_email_pending"))
    except BadSignature:
        flash("Liên kết xác minh không hợp lệ.", "error")
        return redirect(url_for("login"))
    user = db.session.get(User, payload.get("user_id"))
    if not user or user.email != payload.get("email"):
        flash("Liên kết xác minh không hợp lệ.", "error")
        return redirect(url_for("login"))
    if not user.email_verified:
        user.email_verified = True
        user.email_verified_at = utc_now_naive()
        db.session.commit()
    ensure_user_data(user)
    login_user(user)
    flash("Email đã được xác minh thành công.", "success")
    return redirect(url_for("overview"))


@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("login"))


@app.route("/")
@login_required
def overview():
    return render_template("overview.html", user=current_user)


@app.route("/transactions")
@login_required
def transactions():
    return render_template("transactions.html", user=current_user)


@app.route("/budgets")
@login_required
def budgets():
    return render_template("budgets.html", user=current_user)


@app.route("/goals")
@login_required
def goals():
    return render_template("goals.html", user=current_user, goals=Goal.query.filter_by(user_id=current_user.id).all())


@app.route("/ai-coach")
@login_required
def ai_coach():
    return render_template("ai-coach.html", user=current_user)


@app.route("/settings")
@login_required
def settings():
    return render_template("settings.html", user=current_user)


@app.route("/api/account/preferences", methods=["PATCH"])
@login_required
def update_account_preferences():
    data = request.get_json(silent=True) or {}
    for field in ("weekly_email_enabled", "budget_alerts_enabled"):
        if field in data:
            if not isinstance(data[field], bool):
                return json_error("Giá trị tùy chọn không hợp lệ.")
            setattr(current_user, field, data[field])
    db.session.commit()
    return jsonify({
        "success": True,
        "weekly_email_enabled": current_user.weekly_email_enabled,
        "budget_alerts_enabled": current_user.budget_alerts_enabled,
    })


@app.route("/api/account", methods=["DELETE"])
@login_required
def delete_account():
    data = request.get_json(silent=True) or {}
    if data.get("confirmation") != "DELETE":
        return json_error('Vui lòng nhập chính xác "DELETE" để xác nhận.')
    if not check_password_hash(current_user.password_hash, str(data.get("password", ""))):
        return json_error("Mật khẩu không chính xác.")

    user_id = current_user.id
    logout_user()
    try:
        Transaction.query.filter_by(user_id=user_id).delete(synchronize_session=False)
        Budget.query.filter_by(user_id=user_id).delete(synchronize_session=False)
        Goal.query.filter_by(user_id=user_id).delete(synchronize_session=False)
        Account.query.filter_by(user_id=user_id).delete(synchronize_session=False)
        User.query.filter_by(id=user_id).delete(synchronize_session=False)
        db.session.commit()
    except Exception:
        db.session.rollback()
        app.logger.exception("Account deletion failed")
        return json_error("Không thể xóa tài khoản lúc này. Vui lòng thử lại.", 500)
    return jsonify({"success": True, "redirect": url_for("login")})


@app.route("/api/state")
@login_required
def get_state():
    return jsonify(build_state(current_user, request.args.get("period")))


@app.route("/api/accounts/<int:account_id>/balance", methods=["PATCH"])
@login_required
def update_account_balance(account_id):
    data = request.get_json(silent=True) or {}
    try:
        raw_balance = float(data.get("balance"))
    except (TypeError, ValueError):
        return json_error("Số dư không hợp lệ.")
    if not math.isfinite(raw_balance) or raw_balance < 0:
        return json_error("Số dư phải là số không âm.")
    target_balance = round(raw_balance)

    account = Account.query.filter_by(id=account_id, user_id=current_user.id).first()
    if not account:
        return json_error("Không tìm thấy tài khoản.", 404)

    # Preserve the complete transaction history. The opening balance is adjusted
    # so opening balance + all transaction deltas equals the requested balance.
    account.opening_balance = target_balance - account_transaction_delta(account)
    db.session.commit()
    return jsonify({
        "success": True,
        "state": build_state(current_user, data.get("period")),
    })


@app.route("/api/transactions", methods=["GET"])
@login_required
def get_transactions():
    rows = (
        Transaction.query.filter_by(user_id=current_user.id)
        .order_by(Transaction.date.desc(), Transaction.id.desc()).all()
    )
    return jsonify([serialize_transaction(tx) for tx in rows])


@app.route("/api/transactions", methods=["POST"])
@login_required
def add_transaction():
    data = request.get_json(silent=True) or {}
    merchant = str(data.get("merchant") or data.get("note") or "").strip()
    try:
        amount = round(abs(float(data.get("amount", 0))))
        account_id = int(data.get("account_id"))
        category_id = int(data.get("category_id"))
    except (TypeError, ValueError):
        return json_error("Dữ liệu giao dịch không hợp lệ.")
    tx_type = data.get("type")
    tx_date = str(data.get("date") or date.today().isoformat())
    if not merchant:
        return json_error("Vui lòng nhập tên giao dịch.")
    if amount <= 0:
        return json_error("Số tiền phải lớn hơn 0.")
    try:
        datetime.strptime(tx_date, "%Y-%m-%d")
    except ValueError:
        return json_error("Ngày giao dịch không hợp lệ.")
    account = Account.query.filter_by(id=account_id, user_id=current_user.id).first()
    category = db.session.get(Category, category_id)
    if not account or not category or tx_type not in ("income", "expense") or category.kind != tx_type:
        return json_error("Tài khoản, danh mục hoặc loại giao dịch không hợp lệ.")
    signed_amount = amount if tx_type == "income" else -amount
    if account_balance(account) + signed_amount < 0:
        return json_error(f"Số dư {account.name} không đủ.")

    budget_row = None
    previous_spent = 0
    if tx_type == "expense":
        budget_row = Budget.query.filter_by(
            user_id=current_user.id, category_id=category.id
        ).first()
        if budget_row:
            previous_spent = -float(
                db.session.query(db.func.coalesce(db.func.sum(Transaction.amount), 0))
                .filter(
                    Transaction.user_id == current_user.id,
                    Transaction.category_id == category.id,
                    Transaction.date.like(f"{tx_date[:7]}%"),
                    Transaction.amount < 0,
                )
                .scalar()
            )

    tx = Transaction(
        user_id=current_user.id, account_id=account.id, category_id=category.id,
        merchant=merchant, amount=signed_amount, date=tx_date,
        ai_tagged=bool(data.get("ai_tagged")),
    )
    db.session.add(tx)
    db.session.commit()

    state = build_state(current_user, tx_date[:7])
    budget = next((b for b in state["budgets"] if b["category_id"] == category.id), None)
    breach = None
    if tx_type == "expense" and budget and budget["over"] > 0:
        breach = {
            "category": budget["category"], "spent": budget["spent"],
            "limit": budget["limit_vnd"], "over": budget["over"],
        }
        crossed_limit = budget_row and previous_spent <= budget_row.limit_vnd
        if (
            crossed_limit
            and current_user.email_verified
            and current_user.budget_alerts_enabled
            and send_budget_alert_email
            and email_delivery_configured()
        ):
            try:
                send_budget_alert_email(
                    current_user.email,
                    current_user.username,
                    category.name,
                    budget["spent"],
                    budget["limit_vnd"],
                    idempotency_key=(
                        f"budget-{current_user.id}-{category.id}-{tx_date[:7]}-{tx.id}"
                    ),
                )
            except Exception:
                app.logger.exception("Budget alert email failed")
    return jsonify({"success": True, "id": tx.id, "state": state, "breachAlert": breach}), 201


@app.route("/api/transactions/<int:transaction_id>", methods=["DELETE"])
@login_required
def delete_transaction(transaction_id):
    tx = Transaction.query.filter_by(id=transaction_id, user_id=current_user.id).first()
    if not tx:
        return json_error("Không tìm thấy giao dịch.", 404)
    period = tx.date[:7]
    db.session.delete(tx)
    db.session.commit()
    return jsonify(build_state(current_user, period))


@app.route("/api/coach", methods=["POST"])
@login_required
def coach():
    message = str((request.get_json(silent=True) or {}).get("message", "")).strip()
    if not message:
        return json_error("Vui lòng nhập câu hỏi.")
    state = build_state(current_user)
    client = openai_client()
    if client:
        try:
            compact = {
                "kpi": state["kpi"], "accounts": state["accounts"],
                "budgets": state["budgets"], "goals": state["goals"],
                "recent_transactions": state["transactions"][:20],
            }
            response = client.responses.create(
                model=os.environ.get("OPENAI_MODEL", "gpt-5.6-luna"),
                reasoning={"effort": "low"},
                safety_identifier=hashlib.sha256(
                    f"budget-buddy-user:{current_user.id}".encode()
                ).hexdigest(),
                input=[{
                    "role": "user",
                    "content": (
                        "Bạn là trợ lý tài chính cá nhân. Trả lời tiếng Việt, tối đa 120 từ, "
                        "dựa đúng dữ liệu; không bịa số. Nêu 1-3 hành động cụ thể. "
                        f"Dữ liệu: {json.dumps(compact, ensure_ascii=False)}\nCâu hỏi: {message}"
                    ),
                }],
            )
            return jsonify({"reply": response.output_text, "source": "openai"})
        except Exception:
            app.logger.exception("AI Coach failed; using local insight engine")
    return jsonify({"reply": local_coach_reply(message, state), "source": "local"})


@app.route("/api/scan-receipt", methods=["POST"])
@login_required
def scan_receipt():
    receipt = request.files.get("receipt")
    if not receipt or not receipt.filename:
        return json_error("Vui lòng chọn ảnh hóa đơn.")
    if receipt.mimetype not in {"image/jpeg", "image/png", "image/webp"}:
        return json_error("Chỉ hỗ trợ ảnh JPG, PNG hoặc WebP.")
    client = openai_client()
    if not client:
        return json_error("OCR AI chưa được cấu hình. Hãy đặt biến OPENAI_API_KEY.", 503)
    raw = receipt.read()
    if not raw:
        return json_error("Ảnh hóa đơn trống.")
    data_url = f"data:{receipt.mimetype};base64,{base64.b64encode(raw).decode('ascii')}"
    category_names = [c.name for c in Category.query.filter_by(kind="expense").all()]
    schema = {
        "type": "object",
        "properties": {
            "merchant": {"type": "string"},
            "amount": {"type": "number"},
            "date": {"type": "string"},
            "category": {"type": "string", "enum": category_names},
        },
        "required": ["merchant", "amount", "date", "category"],
        "additionalProperties": False,
    }
    try:
        response = client.responses.create(
            model=os.environ.get("OPENAI_MODEL", "gpt-5.6-luna"),
            reasoning={"effort": "low"},
            safety_identifier=hashlib.sha256(
                f"budget-buddy-user:{current_user.id}".encode()
            ).hexdigest(),
            input=[{
                "role": "user",
                "content": [
                    {
                        "type": "input_text",
                        "text": (
                            "Đọc hóa đơn Việt Nam này. Lấy tên cửa hàng, tổng tiền cuối cùng "
                            "(VND, chỉ số), ngày YYYY-MM-DD và chọn danh mục phù hợp. "
                            "Không dùng số tiền của từng món. Nếu không thấy ngày, dùng hôm nay."
                        ),
                    },
                    {"type": "input_image", "image_url": data_url, "detail": "high"},
                ],
            }],
            text={"format": {"type": "json_schema", "name": "receipt", "strict": True, "schema": schema}},
        )
        result = extract_json(response.output_text)
        result["amount"] = round(abs(float(result["amount"])))
        if result["amount"] <= 0:
            raise ValueError("invalid amount")
        try:
            datetime.strptime(result["date"], "%Y-%m-%d")
        except ValueError:
            result["date"] = date.today().isoformat()
        return jsonify(result)
    except Exception:
        app.logger.exception("Receipt OCR failed")
        return json_error("Không thể đọc hóa đơn này. Hãy chụp rõ toàn bộ hóa đơn và thử lại.", 422)


@app.route("/api/goals", methods=["GET"])
@login_required
def get_goals():
    return jsonify(build_state(current_user)["goals"])


@app.route("/api/goals", methods=["POST"])
@login_required
def add_goal():
    data = request.get_json(silent=True) or {}
    try:
        target = float(data.get("target", 0))
        saved = float(data.get("current_saved", data.get("saved", 0)))
    except (TypeError, ValueError):
        return json_error("Số tiền mục tiêu không hợp lệ.")
    name = str(data.get("name", "")).strip()
    if not name or target <= 0 or saved < 0:
        return json_error("Thông tin mục tiêu không hợp lệ.")
    goal = Goal(
        user_id=current_user.id, name=name, target=target, current_saved=saved,
        deadline=str(data.get("deadline", "")).strip()[:30],
        icon=str(data.get("icon", "🎯"))[:10],
        accent=str(data.get("accent", "#0D9488"))[:10],
    )
    db.session.add(goal)
    db.session.commit()
    return jsonify({"success": True, "id": goal.id, "state": build_state(current_user)}), 201


@app.route("/api/goals/<int:goal_id>/deposit", methods=["POST"])
@login_required
def deposit_goal(goal_id):
    goal = Goal.query.filter_by(id=goal_id, user_id=current_user.id).first()
    if not goal:
        return json_error("Không tìm thấy mục tiêu.", 404)
    try:
        amount = float((request.get_json(silent=True) or {}).get("amount", 0))
    except (TypeError, ValueError):
        return json_error("Số tiền không hợp lệ.")
    if amount <= 0:
        return json_error("Số tiền phải lớn hơn 0.")
    goal.current_saved += amount
    db.session.commit()
    if (
        send_goal_plan_email
        and current_user.email
        and current_user.email_verified
        and email_delivery_configured()
    ):
        try:
            remaining = max(0, goal.target - goal.current_saved)
            monthly_needed = 1500000
            send_goal_plan_email(
                current_user.email, current_user.username, goal.name, goal.target,
                goal.current_saved, monthly_needed,
                max(1, int(remaining / monthly_needed)) if remaining else 0,
            )
        except Exception:
            app.logger.exception("Goal email notification failed")
    return jsonify(build_state(current_user))


def send_due_weekly_reports(reference_date=None, force=False):
    """Send each verified user one report for the most recently completed week."""
    if reference_date is None:
        try:
            timezone = ZoneInfo(os.environ.get("APP_TIMEZONE", "Asia/Ho_Chi_Minh"))
        except ZoneInfoNotFoundError:
            app.logger.warning("Unknown APP_TIMEZONE; falling back to UTC")
            timezone = UTC
        reference_date = datetime.now(timezone).date()
    current_monday = reference_date - timedelta(days=reference_date.weekday())
    week_end = current_monday - timedelta(days=1)
    week_start = week_end - timedelta(days=6)
    previous_end = week_start - timedelta(days=1)
    previous_start = previous_end - timedelta(days=6)
    result = {
        "sent": 0,
        "failed": 0,
        "skipped": 0,
        "week_start": week_start.isoformat(),
        "week_end": week_end.isoformat(),
    }

    users = User.query.filter_by(email_verified=True, weekly_email_enabled=True).all()
    for user in users:
        if (
            not force
            and user.last_weekly_email_at
            and user.last_weekly_email_at.date() >= current_monday
        ):
            result["skipped"] += 1
            continue
        weekly_transactions = (
            Transaction.query.filter(
                Transaction.user_id == user.id,
                Transaction.date >= week_start.isoformat(),
                Transaction.date <= week_end.isoformat(),
            )
            .order_by(Transaction.date.desc(), Transaction.id.desc())
            .all()
        )
        previous_transactions = Transaction.query.filter(
            Transaction.user_id == user.id,
            Transaction.date >= previous_start.isoformat(),
            Transaction.date <= previous_end.isoformat(),
        ).all()
        income = sum(tx.amount for tx in weekly_transactions if tx.amount > 0)
        expense = -sum(tx.amount for tx in weekly_transactions if tx.amount < 0)
        previous_expense = -sum(tx.amount for tx in previous_transactions if tx.amount < 0)
        categories = {category.id: category.name for category in Category.query.all()}
        by_category = {}
        for tx in weekly_transactions:
            if tx.amount < 0:
                name = categories.get(tx.category_id, "Khác")
                by_category[name] = by_category.get(name, 0) - tx.amount
        recent = [
            {"date": tx.date, "merchant": tx.merchant, "amount": float(tx.amount)}
            for tx in weekly_transactions
        ]
        delivered = False
        if send_weekly_summary_email and email_delivery_configured():
            try:
                delivered = send_weekly_summary_email(
                    user.email,
                    user.username,
                    week_start.isoformat(),
                    week_end.isoformat(),
                    income,
                    expense,
                    previous_expense,
                    by_category,
                    recent,
                    idempotency_key=f"weekly-{user.id}-{week_start.isoformat()}",
                )
            except Exception:
                app.logger.exception("Weekly email failed for user %s", user.id)
        if delivered:
            user.last_weekly_email_at = datetime(
                current_monday.year, current_monday.month, current_monday.day
            )
            db.session.commit()
            result["sent"] += 1
        else:
            result["failed"] += 1
    return result


@app.cli.command("send-weekly-reports")
@click.option("--force", is_flag=True, help="Send again even if this week's report was sent.")
def send_weekly_reports_command(force):
    result = send_due_weekly_reports(force=force)
    click.echo(json.dumps(result, ensure_ascii=False))


with app.app_context():
    upgrade_user_schema()
    legacy_tables = prepare_legacy_tables()
    db.create_all()
    seed_categories()
    migrate_legacy_data(legacy_tables)


if __name__ == "__main__":
    app.run(debug=os.environ.get("FLASK_DEBUG") == "1")
