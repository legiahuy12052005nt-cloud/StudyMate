import unittest
from helper import build_prompt, validate_text

class HelperTests(unittest.TestCase):
    def test_empty(self):
        self.assertIsNotNone(validate_text(" "))

    def test_valid(self):
        self.assertIsNone(validate_text("Bài học Python."))

    def test_over_limit(self):
        self.assertIsNotNone(validate_text("x" * 10001))

    def test_prompt(self):
        self.assertIn("Bài học Python", build_prompt("Bài học Python"))

if __name__ == "__main__":
    unittest.main()
