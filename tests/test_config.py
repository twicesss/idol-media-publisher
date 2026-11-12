import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class AccountConfigTests(unittest.TestCase):
    def test_accounts_config_is_valid_and_unique(self):
        config = json.loads((ROOT / "config" / "accounts.json").read_text(encoding="utf-8"))
        accounts = config["accounts"]
        self.assertIsInstance(accounts, list)
        self.assertGreaterEqual(len(accounts), 1)
        self.assertEqual(len(accounts), len(set(accounts)))
        self.assertTrue(all(isinstance(handle, str) and handle.strip() for handle in accounts))

    def test_initial_accounts_are_present(self):
        config = json.loads((ROOT / "config" / "accounts.json").read_text(encoding="utf-8"))
        self.assertEqual(config["accounts"], ["WithPJihyo", "hyoluvsite", "zyo_0201", "parkjihyoo__"])

    def test_poll_interval_is_positive(self):
        config = json.loads((ROOT / "config" / "accounts.json").read_text(encoding="utf-8"))
        self.assertGreater(config["poll_interval_minutes"], 0)


if __name__ == "__main__":
    unittest.main()
