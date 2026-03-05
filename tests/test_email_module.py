import unittest

from modules.email_module import find_email


class EmailModuleTests(unittest.TestCase):
    def test_find_email_from_bio(self):
        profile = {"bio": "Reach me at hello@example.com for collab"}
        self.assertEqual(find_email(profile), "hello@example.com")

    def test_find_email_from_website_text(self):
        profile = {"bio": "", "website": "contact: team@brand.co"}
        self.assertEqual(find_email(profile), "team@brand.co")


if __name__ == "__main__":
    unittest.main()
