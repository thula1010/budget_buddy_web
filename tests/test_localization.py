import unittest

from utils.email_templates import alert_template, format_money


class LocalizationTemplateTest(unittest.TestCase):
    def test_money_conversion_formats_vnd_and_usd(self):
        self.assertEqual(format_money(250_000, "VND", 25_000), "250.000 ₫")
        self.assertEqual(format_money(250_000, "USD", 25_000), "$10.00")

    def test_budget_alert_matches_vietnamese_vnd_preferences(self):
        html = alert_template(
            "An", "Food & Drinks", 650_000, 600_000,
            language="vi", currency="VND", usd_vnd_rate=25_000,
        )
        self.assertIn('lang="vi"', html)
        self.assertIn("Ăn uống", html)
        self.assertIn("650.000 ₫", html)
        self.assertIn("50.000 ₫", html)

    def test_budget_alert_matches_english_usd_preferences(self):
        html = alert_template(
            "An", "Food & Drinks", 650_000, 600_000,
            language="en", currency="USD", usd_vnd_rate=25_000,
        )
        self.assertIn('lang="en"', html)
        self.assertIn("Budget limit exceeded", html)
        self.assertIn("$26.00", html)
        self.assertIn("$2.00", html)


if __name__ == "__main__":
    unittest.main()
