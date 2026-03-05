import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


class DatabaseTests(unittest.TestCase):
    def test_upsert_stats_campaign_pool_and_quota(self):
        with tempfile.TemporaryDirectory() as td:
            db_file = Path(td) / "pool.db"
            import modules.database as db

            with patch.object(db, "DB_PATH", db_file):
                db.init_db()
                self.assertTrue(db_file.exists())

                _id = db.upsert_influencer(
                    {
                        "username": "testuser",
                        "followers": 1200,
                        "bio": "dijital pazarlama uzmanı",
                        "email": "test@example.com",
                        "niche_tags": ["marketing", "smb"],
                    }
                )
                self.assertTrue(_id > 0)

                stats = db.get_stats()
                self.assertEqual(stats["discovered"], 1)

                db.update_influencer("testuser", status="partner", ai_score=9.1)
                stats = db.get_stats()
                self.assertEqual(stats["partner"], 1)
                partners = db.get_partners()
                self.assertEqual(len(partners), 1)
                self.assertEqual(partners[0]["username"], "testuser")

                db.log_email(influencer_username="testuser", direction="outbound", subject="s", body="b")
                self.assertEqual(db.get_outbound_count_today(), 1)

                pool = db.find_candidate_pool("pazarlama hizmeti", limit=10, min_ai_score=1.0)
                self.assertGreaterEqual(len(pool), 1)
                self.assertEqual(pool[0]["username"], "testuser")


if __name__ == "__main__":
    unittest.main()
