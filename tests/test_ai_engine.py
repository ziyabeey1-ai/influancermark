import unittest
from unittest.mock import patch

import modules.ai_engine as ai


class AiEngineTests(unittest.TestCase):
    def test_analyze_profile_fallback(self):
        with patch.object(ai, "_get_model", return_value=(False, None)):
            res = ai.analyze_profile({"followers": 2000}, ["marketing"])
            self.assertIn("score", res)
            self.assertTrue(res["suitable"])

    def test_generate_strategy_email_fallback(self):
        with patch.object(ai, "_get_model", return_value=(False, None)):
            email = ai.generate_strategy_email(
                profile={"username": "demo", "full_name": "Demo User"},
                ai_analysis={"score": 7},
                product_or_service="Yeni SaaS ürünü",
                strategy_type="budget",
                budget_info="5.000-10.000 TL",
            )
            self.assertIn("subject", email)
            self.assertIn("body", email)
            self.assertIn("5.000-10.000", email["body"])


if __name__ == "__main__":
    unittest.main()
