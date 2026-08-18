"""Kiểm thử ba tính năng mới: ngôn ngữ/tiền tệ, lịch sử AI Coach, quản lý tài khoản."""

import os
import sys
import tempfile
import unittest


# `app` chỉ được import một lần cho cả bộ test. Nếu module khác đã import trước,
# ta dùng chung database của module đó thay vì tranh nhau biến môi trường.
if "app" not in sys.modules:
    TEST_DIR = tempfile.TemporaryDirectory()
    os.environ["DATABASE_URL"] = (
        "sqlite:///" + os.path.join(TEST_DIR.name, "features.db").replace("\\", "/")
    )
    os.environ.pop("OPENAI_API_KEY", None)
    os.environ["EMAIL_VERIFICATION_REQUIRED"] = "0"
else:
    TEST_DIR = None

import app as app_module  # noqa: E402
from app import app, db  # noqa: E402


def setUpModule():
    """Đảm bảo database còn tồn tại kể cả khi module test chạy trước đã dọn dẹp."""
    app.config["EMAIL_VERIFICATION_REQUIRED"] = False
    uri = app.config["SQLALCHEMY_DATABASE_URI"]
    if uri.startswith("sqlite:///"):
        folder = os.path.dirname(uri[len("sqlite:///"):])
        if folder:
            os.makedirs(folder, exist_ok=True)
    with app.app_context():
        db.create_all()
        app_module.seed_categories()


def tearDownModule():
    with app.app_context():
        db.session.remove()
        db.engine.dispose()
    if TEST_DIR is not None:
        TEST_DIR.cleanup()


class FeatureTestBase(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()

    def register(self, username):
        self.client.post(
            "/api/signup",
            data={
                "username": username,
                "email": f"{username}@example.com",
                "password": "password123",
                "confirm_password": "password123",
            },
        )
        self.client.post("/api/login", data={"username": username, "password": "password123"})

    def state(self):
        return self.client.get("/api/state").get_json()


class LanguageAndCurrencyTest(FeatureTestBase):
    def test_defaults_are_vietnamese_and_dong(self):
        self.register("lang_default")
        prefs = self.state()["prefs"]
        self.assertEqual(prefs["language"], "vi")
        self.assertEqual(prefs["currency"], "VND")
        self.assertIn("USD", [c["code"] for c in prefs["currencies"]])

    def test_preferences_persist_and_reject_unknown_values(self):
        self.register("lang_switch")

        saved = self.client.patch(
            "/api/account/preferences", json={"language": "en", "currency": "USD"}
        )
        self.assertEqual(saved.status_code, 200)
        self.assertEqual(self.state()["prefs"], self.state()["prefs"])
        self.assertEqual(self.state()["user"]["language"], "en")
        self.assertEqual(self.state()["user"]["currency"], "USD")

        self.assertEqual(
            self.client.patch("/api/account/preferences", json={"language": "fr"}).status_code, 400
        )
        self.assertEqual(
            self.client.patch("/api/account/preferences", json={"currency": "BTC"}).status_code, 400
        )
        # Giá trị hợp lệ trước đó không bị ghi đè bởi yêu cầu lỗi.
        self.assertEqual(self.state()["user"]["language"], "en")

    def test_amounts_are_stored_in_dong_and_only_formatting_changes(self):
        self.register("lang_money")
        balance_vnd = self.state()["kpi"]["balance"]

        self.client.patch("/api/account/preferences", json={"language": "en", "currency": "USD"})
        after_switch = self.state()["kpi"]["balance"]
        self.assertEqual(balance_vnd, after_switch)

        formatted = app_module.format_money(balance_vnd, "USD", "en")
        self.assertTrue(formatted.startswith("$"))
        self.assertAlmostEqual(
            float(formatted[1:].replace(",", "")),
            balance_vnd / app_module.CURRENCY_RATES["USD"],
            places=2,
        )
        self.assertEqual(app_module.format_money(1450000, "VND", "vi"), "1.450.000 ₫")

    def test_coach_and_errors_follow_the_chosen_language(self):
        self.register("lang_coach")

        vi = self.client.post("/api/coach", json={"message": "Số dư tài khoản?"}).get_json()
        self.assertIn("Số dư hiện tại", vi["reply"])

        self.client.patch("/api/account/preferences", json={"language": "en", "currency": "USD"})
        en = self.client.post("/api/coach", json={"message": "account balance?"}).get_json()
        self.assertIn("Current balances", en["reply"])
        self.assertIn("$", en["reply"])

        error = self.client.post("/api/accounts", json={"name": "", "type": "bank"}).get_json()
        self.assertEqual(error["error"], "Please enter an account name.")


class ChatHistoryTest(FeatureTestBase):
    def test_messages_are_stored_and_grouped_into_sessions(self):
        self.register("chat_store")

        first = self.client.post("/api/coach", json={"message": "Tôi tiêu bao nhiêu?"}).get_json()
        session_id = first["session"]["id"]
        self.assertEqual(first["session"]["message_count"], 2)

        self.client.post(
            "/api/coach", json={"message": "Còn ngân sách?", "session_id": session_id}
        )
        detail = self.client.get(f"/api/chat/sessions/{session_id}").get_json()
        self.assertEqual([m["role"] for m in detail["messages"]], ["user", "ai", "user", "ai"])
        self.assertEqual(detail["messages"][0]["text"], "Tôi tiêu bao nhiêu?")

        # Không truyền session_id sẽ mở một cuộc trò chuyện mới.
        second = self.client.post("/api/coach", json={"message": "Chủ đề khác"}).get_json()
        self.assertNotEqual(second["session"]["id"], session_id)
        self.assertEqual(len(self.client.get("/api/chat/sessions").get_json()["sessions"]), 2)

    def test_title_comes_from_the_first_question(self):
        self.register("chat_title")
        created = self.client.post("/api/coach", json={"message": "Mua laptop như thế nào?"}).get_json()
        self.assertEqual(created["session"]["title"], "Mua laptop như thế nào?")

        long_question = "a" * 200
        long_session = self.client.post("/api/coach", json={"message": long_question}).get_json()
        self.assertLessEqual(len(long_session["session"]["title"]), app_module.CHAT_TITLE_MAX)

    def test_rename_delete_and_clear(self):
        self.register("chat_manage")
        session_id = self.client.post("/api/coach", json={"message": "Xin chào"}).get_json()["session"]["id"]

        renamed = self.client.patch(f"/api/chat/sessions/{session_id}", json={"title": "Kế hoạch"})
        self.assertEqual(renamed.get_json()["session"]["title"], "Kế hoạch")
        self.assertEqual(
            self.client.patch(f"/api/chat/sessions/{session_id}", json={"title": "  "}).status_code, 400
        )

        self.client.post("/api/coach", json={"message": "Câu khác"})
        self.assertEqual(self.client.delete(f"/api/chat/sessions/{session_id}").status_code, 200)
        self.assertEqual(len(self.client.get("/api/chat/sessions").get_json()["sessions"]), 1)

        self.client.delete("/api/chat/sessions")
        self.assertEqual(self.client.get("/api/chat/sessions").get_json()["sessions"], [])
        with app.app_context():
            owner = app_module.User.query.filter_by(username="chat_manage").first()
            self.assertEqual(app_module.ChatMessage.query.filter_by(user_id=owner.id).count(), 0)
            self.assertEqual(app_module.ChatSession.query.filter_by(user_id=owner.id).count(), 0)

    def test_history_is_private_to_each_user(self):
        self.register("chat_owner")
        owner_session = self.client.post("/api/coach", json={"message": "Riêng tư"}).get_json()["session"]["id"]
        self.client.get("/logout")

        self.register("chat_intruder")
        self.assertEqual(self.client.get(f"/api/chat/sessions/{owner_session}").status_code, 404)
        self.assertEqual(self.client.delete(f"/api/chat/sessions/{owner_session}").status_code, 404)
        self.assertEqual(self.client.get("/api/chat/sessions").get_json()["sessions"], [])


class AccountManagementTest(FeatureTestBase):
    def test_create_account_validates_input(self):
        self.register("acc_create")

        created = self.client.post(
            "/api/accounts",
            json={"name": "Vietcombank", "type": "bank", "icon": "\U0001f3db", "opening_balance": 2000000},
        )
        self.assertEqual(created.status_code, 201)
        names = [a["name"] for a in created.get_json()["state"]["accounts"]]
        self.assertIn("Vietcombank", names)

        self.assertEqual(
            self.client.post("/api/accounts", json={"name": "  vietcombank ", "type": "bank"}).status_code,
            400,
        )
        self.assertEqual(
            self.client.post("/api/accounts", json={"name": "Ví lạ", "type": "crypto"}).status_code, 400
        )
        self.assertEqual(
            self.client.post("/api/accounts", json={"name": "Ví âm", "type": "cash", "opening_balance": -5}).status_code,
            400,
        )

    def test_new_account_balance_counts_towards_the_total(self):
        self.register("acc_total")
        before = self.state()["kpi"]["balance"]
        self.client.post(
            "/api/accounts", json={"name": "Sổ tiết kiệm", "type": "savings", "opening_balance": 3000000}
        )
        self.assertEqual(self.state()["kpi"]["balance"], before + 3000000)

    def test_rename_and_retype_an_account(self):
        self.register("acc_edit")
        account_id = self.client.post(
            "/api/accounts", json={"name": "MoMo 2", "type": "ewallet"}
        ).get_json()["account_id"]

        updated = self.client.patch(
            f"/api/accounts/{account_id}", json={"name": "ZaloPay", "type": "ewallet", "icon": "\U0001f4b3"}
        )
        self.assertEqual(updated.status_code, 200)
        account = next(a for a in updated.get_json()["state"]["accounts"] if a["id"] == account_id)
        self.assertEqual(account["name"], "ZaloPay")
        self.assertEqual(account["icon"], "\U0001f4b3")

    def test_delete_moves_history_and_keeps_the_total_balance(self):
        self.register("acc_delete")
        state = self.state()
        account_id = self.client.post(
            "/api/accounts", json={"name": "Tạm", "type": "bank", "opening_balance": 1000000}
        ).get_json()["account_id"]
        category_id = state["categories"][0]["id"]

        self.client.post(
            "/api/transactions",
            json={
                "merchant": "Test",
                "amount": 100000,
                "date": f"{state['period']}-05",
                "type": "expense",
                "category_id": category_id,
                "account_id": account_id,
            },
        )
        total_before = self.state()["kpi"]["balance"]

        blocked = self.client.delete(f"/api/accounts/{account_id}", json={})
        self.assertEqual(blocked.status_code, 400)

        target = next(a["id"] for a in self.state()["accounts"] if a["id"] != account_id)
        removed = self.client.delete(f"/api/accounts/{account_id}", json={"move_to": target})
        self.assertEqual(removed.status_code, 200)
        self.assertEqual(removed.get_json()["moved_transactions"], 1)

        after = self.state()
        self.assertEqual(after["kpi"]["balance"], total_before)
        self.assertNotIn(account_id, [a["id"] for a in after["accounts"]])
        self.assertTrue(all(t["account_id"] == target for t in after["transactions"]))

    def test_last_account_cannot_be_deleted(self):
        self.register("acc_last")
        accounts = self.state()["accounts"]
        keep = accounts[0]["id"]
        for account in accounts[1:]:
            self.client.delete(f"/api/accounts/{account['id']}", json={})
        self.assertEqual(self.client.delete(f"/api/accounts/{keep}", json={}).status_code, 400)
        self.assertEqual(len(self.state()["accounts"]), 1)

    def test_accounts_are_private_to_each_user(self):
        self.register("acc_owner")
        owner_account = self.client.post(
            "/api/accounts", json={"name": "Riêng", "type": "bank"}
        ).get_json()["account_id"]
        self.client.get("/logout")

        self.register("acc_intruder")
        self.assertEqual(self.client.patch(f"/api/accounts/{owner_account}", json={"name": "X"}).status_code, 404)
        self.assertEqual(self.client.delete(f"/api/accounts/{owner_account}", json={}).status_code, 404)


if __name__ == "__main__":
    unittest.main()
