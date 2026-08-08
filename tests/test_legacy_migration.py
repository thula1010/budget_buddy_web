import os
import sqlite3
import subprocess
import sys
import tempfile
import unittest


class LegacyMigrationTest(unittest.TestCase):
    def test_original_database_is_upgraded_without_losing_rows(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            database_path = os.path.join(temp_dir, "legacy.db")
            connection = sqlite3.connect(database_path)
            connection.executescript(
                """
                CREATE TABLE user (
                    id INTEGER PRIMARY KEY,
                    username VARCHAR(80) NOT NULL UNIQUE,
                    email VARCHAR(120) NOT NULL UNIQUE,
                    password_hash VARCHAR(200) NOT NULL
                );
                CREATE TABLE "transaction" (
                    id INTEGER PRIMARY KEY,
                    amount FLOAT NOT NULL,
                    category VARCHAR(100) NOT NULL,
                    type VARCHAR(20) NOT NULL,
                    note VARCHAR(200),
                    date VARCHAR(50) NOT NULL
                );
                CREATE TABLE goal (
                    id INTEGER PRIMARY KEY,
                    name VARCHAR(100) NOT NULL,
                    target FLOAT NOT NULL,
                    current_saved FLOAT
                );
                INSERT INTO user VALUES (1, 'legacy-user', 'legacy@example.com', 'unused');
                INSERT INTO "transaction" VALUES
                    (1, 45000, 'Food & Drinks', 'expense', 'Giao dịch cũ', '2026-08-01');
                INSERT INTO goal VALUES (1, 'Quỹ khẩn cấp', 10000000, 2500000);
                """
            )
            connection.commit()
            connection.close()

            env = os.environ.copy()
            env["DATABASE_URL"] = "sqlite:///" + database_path.replace("\\", "/")
            env.pop("OPENAI_API_KEY", None)
            completed = subprocess.run(
                [sys.executable, "-c", "import app"],
                cwd=os.path.dirname(os.path.dirname(__file__)),
                env=env,
                capture_output=True,
                text=True,
                timeout=30,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)

            connection = sqlite3.connect(database_path)
            transaction = connection.execute(
                'SELECT merchant, amount, user_id FROM "transaction"'
            ).fetchone()
            goal = connection.execute(
                "SELECT name, current_saved, user_id, icon FROM goal"
            ).fetchone()
            tables = {
                row[0] for row in connection.execute(
                    "SELECT name FROM sqlite_master WHERE type='table'"
                )
            }
            connection.close()

            self.assertEqual(transaction, ("Giao dịch cũ", -45000.0, 1))
            self.assertEqual(goal, ("Quỹ khẩn cấp", 2500000.0, 1, "🎯"))
            self.assertNotIn("transaction_legacy", tables)
            self.assertNotIn("goal_legacy", tables)


if __name__ == "__main__":
    unittest.main()
