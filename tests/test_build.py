"""Tests for build.py — bootstrap test suite."""
import os
import sys
import tempfile
import unittest

# build.py lives one directory up from tests/
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from build import _og_fingerprint, _og_inputs_changed  # noqa: E402


class TestOgImageSkip(unittest.TestCase):
    def test_first_run_always_regenerates(self):
        with tempfile.TemporaryDirectory() as d:
            hash_path = os.path.join(d, ".og-image-hash")
            self.assertTrue(_og_inputs_changed("Nick", "Dev", "https://example.com", hash_path))

    def test_same_inputs_no_regen(self):
        with tempfile.TemporaryDirectory() as d:
            hash_path = os.path.join(d, ".og-image-hash")
            fp = _og_fingerprint("Nick", "Dev", "https://example.com")
            with open(hash_path, "w") as f:
                f.write(fp)
            self.assertFalse(_og_inputs_changed("Nick", "Dev", "https://example.com", hash_path))

    def test_changed_name_triggers_regen(self):
        with tempfile.TemporaryDirectory() as d:
            hash_path = os.path.join(d, ".og-image-hash")
            fp = _og_fingerprint("Nick", "Dev", "https://example.com")
            with open(hash_path, "w") as f:
                f.write(fp)
            self.assertTrue(_og_inputs_changed("Nicholas", "Dev", "https://example.com", hash_path))


if __name__ == "__main__":
    unittest.main()
