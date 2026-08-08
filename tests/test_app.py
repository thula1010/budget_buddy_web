import io
import os
import tempfile
import unittest
from types import SimpleNamespace
from unittest.mock import patch


TEST_DIR = tempfile.TemporaryDirectory()
os.environ["DATABASE_URL"] = "sqlite:///" + os.path.join(TEST_DIR.name, "test.db").replace("\\", "/")
os.environ.pop("OPENAI_API_KEY", None)

import app as app_module  # noqa: E402
from app import app, db  # noqa: E402


class BudgetBuddyIntegrationTest(unittest.TestCase):
    @classmethod
    def tearDownClass(cls):
        with app.app_context():
            db.session.remove()
            db.engine.dispose()
        TEST_DIR.cleanup()

    def setUp(self):
        self.client = app.test_client()

    def signup(self, username, email):
        return self.client.post(
            "/api/signup",
            data={
                "username": username,
                "email": email,
                "password": "password123",
                "confirm_password": "password123",
            },
        )

    def test_transaction_persists_syncs_and_is_user_scoped(self):
        self.signup("alice", "alice@example.com")
        state = self.client.get("/api/state").get_json()
        self.assertEqual(state["kpi"]["balance"], 2_800_000)
        wallet = next(a for a in state["accounts"] if a["name"] == "Personal Wallet")
        food = next(c for c in state["categories"] if c["name"] == "Food & Drinks")

        created = self.client.post(
            "/api/transactions",
            json={
                "merchant": "Quán ăn thử nghiệm",
                "amount": 45_000,
                "date": "2026-08-08",
                "type": "expense",
                "account_id": wallet["id"],
                "category_id": food["id"],
            },
        )
        self.assertEqual(created.status_code, 201)
        transaction_id = created.get_json()["id"]

        refreshed = self.client.get("/api/state?period=2026-08").get_json()
        refreshed_wallet = next(a for a in refreshed["accounts"] if a["id"] == wallet["id"])
        food_budget = next(b for b in refreshed["budgets"] if b["category_id"] == food["id"])
        self.assertEqual(refreshed_wallet["balance"], 475_000)
        self.assertEqual(refreshed["kpi"]["balance"], 2_755_000)
        self.assertEqual(refreshed["transactions"][0]["merchant"], "Quán ăn thử nghiệm")
        self.assertEqual(food_budget["spent"], 45_000)

        self.client.get("/logout")
        self.signup("bob", "bob@example.com")
        bob_state = self.client.get("/api/state?period=2026-08").get_json()
        self.assertEqual(bob_state["transactions"], [])
        self.assertEqual(bob_state["kpi"]["balance"], 2_800_000)
        self.assertEqual(self.client.delete(f"/api/transactions/{transaction_id}").status_code, 404)

        self.client.get("/logout")
        self.client.post("/api/login", data={"username": "alice", "password": "password123"})
        self.assertEqual(len(self.client.get("/api/transactions").get_json()), 1)
        deleted = self.client.delete(f"/api/transactions/{transaction_id}")
        self.assertEqual(deleted.status_code, 200)
        self.assertEqual(deleted.get_json()["kpi"]["balance"], 2_800_000)

    def test_validation_ai_fallback_and_ocr_configuration_error(self):
        self.signup("carol", "carol@example.com")
        state = self.client.get("/api/state").get_json()
        wallet = next(a for a in state["accounts"] if a["name"] == "Personal Wallet")
        food = next(c for c in state["categories"] if c["name"] == "Food & Drinks")
        rejected = self.client.post(
            "/api/transactions",
            json={
                "merchant": "Khoản chi quá số dư",
                "amount": 999_000_000,
                "date": "2026-08-08",
                "type": "expense",
                "account_id": wallet["id"],
                "category_id": food["id"],
            },
        )
        self.assertEqual(rejected.status_code, 400)

        coach = self.client.post("/api/coach", json={"message": "Số dư của tôi?"}).get_json()
        self.assertEqual(coach["source"], "local")
        self.assertIn("2,800,000", coach["reply"])

        ocr = self.client.post(
            "/api/scan-receipt",
            data={"receipt": (io.BytesIO(b"not-a-real-image"), "receipt.png")},
            content_type="multipart/form-data",
        )
        self.assertEqual(ocr.status_code, 503)
        self.assertIn("OPENAI_API_KEY", ocr.get_json()["error"])

    def test_balance_edit_persists_preserves_history_and_is_user_scoped(self):
        self.signup("erin", "erin@example.com")
        state = self.client.get("/api/state?period=2026-08").get_json()
        wallet = next(a for a in state["accounts"] if a["name"] == "Personal Wallet")
        food = next(c for c in state["categories"] if c["name"] == "Food & Drinks")

        created = self.client.post(
            "/api/transactions",
            json={
                "merchant": "Lunch",
                "amount": 20_000,
                "date": "2026-08-08",
                "type": "expense",
                "account_id": wallet["id"],
                "category_id": food["id"],
            },
        )
        self.assertEqual(created.status_code, 201)

        updated = self.client.patch(
            f'/api/accounts/{wallet["id"]}/balance',
            json={"balance": 750_000, "period": "2026-08"},
        )
        self.assertEqual(updated.status_code, 200)
        updated_state = updated.get_json()["state"]
        updated_wallet = next(a for a in updated_state["accounts"] if a["id"] == wallet["id"])
        self.assertEqual(updated_wallet["balance"], 750_000)
        self.assertEqual(updated_state["kpi"]["balance"], 3_030_000)
        self.assertEqual(len(updated_state["transactions"]), 1)

        another_expense = self.client.post(
            "/api/transactions",
            json={
                "merchant": "Dinner",
                "amount": 50_000,
                "date": "2026-08-09",
                "type": "expense",
                "account_id": wallet["id"],
                "category_id": food["id"],
            },
        )
        self.assertEqual(another_expense.status_code, 201)
        refreshed = self.client.get("/api/state?period=2026-08").get_json()
        refreshed_wallet = next(a for a in refreshed["accounts"] if a["id"] == wallet["id"])
        self.assertEqual(refreshed_wallet["balance"], 700_000)
        self.assertEqual(len(refreshed["transactions"]), 2)

        self.client.get("/logout")
        self.signup("frank", "frank@example.com")
        frank_state = self.client.get("/api/state?period=2026-08").get_json()
        frank_wallet = next(a for a in frank_state["accounts"] if a["name"] == "Personal Wallet")
        self.assertEqual(frank_wallet["balance"], 520_000)
        self.assertEqual(frank_state["kpi"]["balance"], 2_800_000)
        self.assertEqual(frank_state["transactions"], [])
        forbidden = self.client.patch(
            f'/api/accounts/{wallet["id"]}/balance', json={"balance": 1_000_000}
        )
        self.assertEqual(forbidden.status_code, 404)

    def test_goals_and_receipt_ocr_response_shape(self):
        self.signup("dana", "dana@example.com")
        created = self.client.post(
            "/api/goals",
            json={
                "name": "Laptop mới",
                "target": 20_000_000,
                "saved": 2_000_000,
                "deadline": "Dec 2027",
                "icon": "💻",
                "accent": "#A78BFA",
            },
        )
        self.assertEqual(created.status_code, 201)
        goal = created.get_json()["state"]["goals"][0]
        self.assertEqual(goal["deadline"], "Dec 2027")
        self.assertEqual(goal["icon"], "💻")
        deposited = self.client.post(
            f'/api/goals/{goal["id"]}/deposit', json={"amount": 500_000}
        )
        self.assertEqual(deposited.status_code, 200)
        self.assertEqual(deposited.get_json()["goals"][0]["saved"], 2_500_000)

        calls = []

        class FakeResponses:
            def create(self, **kwargs):
                calls.append(kwargs)
                return SimpleNamespace(output_text=(
                    '{"merchant":"Siêu thị thử nghiệm","amount":125000,'
                    '"date":"2026-08-08","category":"Shopping"}'
                ))

        fake_client = SimpleNamespace(responses=FakeResponses())
        with patch.object(app_module, "openai_client", return_value=fake_client):
            ocr = self.client.post(
                "/api/scan-receipt",
                data={"receipt": (io.BytesIO(b"image-bytes"), "receipt.png")},
                content_type="multipart/form-data",
            )
        self.assertEqual(ocr.status_code, 200)
        self.assertEqual(ocr.get_json()["amount"], 125_000)
        self.assertEqual(calls[0]["model"], "gpt-5.6-luna")
        self.assertEqual(calls[0]["text"]["format"]["type"], "json_schema")
        self.assertTrue(calls[0]["safety_identifier"])


if __name__ == "__main__":
    unittest.main()
