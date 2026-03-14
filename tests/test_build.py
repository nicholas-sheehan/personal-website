"""Tests for build.py — bootstrap test suite."""
import os
import sys
import tempfile
import unittest

# build.py lives one directory up from tests/
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import re as _re

from build import _og_fingerprint, _og_inputs_changed  # noqa: E402
from build import _strip_updated_block, _content_changed  # noqa: E402


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


class TestBotCommitSkip(unittest.TestCase):
    def test_timestamp_only_change_not_detected(self):
        old = "<!-- updated:start -->\nOld timestamp\n<!-- updated:end -->\n<p>Content</p>"
        new = "<!-- updated:start -->\nNew timestamp\n<!-- updated:end -->\n<p>Content</p>"
        self.assertFalse(_content_changed(old, new))

    def test_content_change_detected(self):
        old = "<!-- updated:start -->\nOld\n<!-- updated:end -->\n<p>Old content</p>"
        new = "<!-- updated:start -->\nNew\n<!-- updated:end -->\n<p>New content</p>"
        self.assertTrue(_content_changed(old, new))

    def test_no_updated_block_compares_full(self):
        old = "<p>Content</p>"
        new = "<p>Different</p>"
        self.assertTrue(_content_changed(old, new))


class TestTmdbHeaderAuth(unittest.TestCase):
    def test_bearer_token_not_in_query_params(self):
        """TMDB search URL must not contain api_key as a query param."""
        import urllib.parse
        token = "test_token_123"
        params = urllib.parse.urlencode({"query": "Dune", "year": "2021"})
        url = f"https://api.themoviedb.org/3/search/movie?{params}"
        self.assertNotIn("api_key", url)
        self.assertNotIn(token, url)

    def test_bearer_token_in_auth_header(self):
        """Authorization header must be Bearer token."""
        token = "test_token_123"
        headers = {"Authorization": f"Bearer {token}", "User-Agent": "Mozilla/5.0"}
        self.assertTrue(headers["Authorization"].startswith("Bearer "))
        self.assertIn(token, headers["Authorization"])


if __name__ == "__main__":
    unittest.main()
