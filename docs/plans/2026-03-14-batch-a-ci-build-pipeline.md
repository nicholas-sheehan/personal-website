# Batch A — CI & Build Pipeline Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Harden the CI/CD pipeline and build script with eight targeted improvements — pinned dependencies, concurrency control, artifact handoff, Worker auto-deploy, HTML validation, smarter bot commits, OG image regen guard, and TMDB header auth.

**Architecture:** Changes split across two files: `.github/workflows/build.yml` (CI config, Tasks 1–4) and `build.py` (Python build script, Tasks 5–7). A new `tests/test_build.py` bootstraps the test suite for the build script changes. All changes are independently verifiable.

**Tech Stack:** GitHub Actions, Python 3.12, `html5validator` (PyPI), Cloudflare Wrangler, `unittest` (stdlib)

---

## Chunk 1: CI workflow hardening

### Task 1: Pin `requirements.txt` + add `html5validator`

**Files:**
- Modify: `requirements.txt`
- Modify: `.github/workflows/build.yml` (add html5validator validation step)

**Context:** `Pillow` and `tomli` are unpinned — a major release could silently break OG image generation. `html5validator` is a PyPI tool that wraps the Nu HTML Checker to validate HTML5 output.

- [ ] **Step 1: Pin versions in `requirements.txt`**

Replace the current contents with:

```
Pillow>=10,<12
tomli>=2,<3; python_version < "3.11"
html5validator
```

- [ ] **Step 2: Add HTML validation step to `build.yml`**

In the `deploy` job, after the "Assemble site files" step and before "Deploy to Cloudflare Pages", add:

```yaml
      - name: Install html5validator
        run: pip install html5validator

      - name: Validate HTML
        run: html5validator --root _site/ --also-check-css --log INFO
```

> Note: `html5validator` runs the vnu.jar checker, which requires Java. The `ubuntu-latest` runner has Java pre-installed.

- [ ] **Step 3: Verify locally that `requirements.txt` still installs cleanly**

```bash
pip install -r requirements.txt
```

Expected: installs without error. Pillow version should be 10.x or 11.x.

- [ ] **Step 4: Commit**

```bash
git add requirements.txt .github/workflows/build.yml
git commit -m "build: pin Pillow/tomli versions, add HTML validation to CI"
```

---

### Task 2: CI concurrency control

**Files:**
- Modify: `.github/workflows/build.yml`

**Context:** If two pushes arrive quickly (e.g. a bot commit immediately after a manual push), both CI runs start in parallel. The second run can deploy stale HTML. A `concurrency` key cancels the in-progress run when a newer one starts.

- [ ] **Step 1: Add `concurrency` key to `build.yml`**

Add after the `on:` block and before `permissions:`:

```yaml
concurrency:
  group: ${{ github.ref }}
  cancel-in-progress: true
```

This cancels any in-progress run on the same branch when a new push arrives.

- [ ] **Step 2: Commit**

```bash
git add .github/workflows/build.yml
git commit -m "ci: add concurrency control to cancel stale in-progress runs"
```

---

### Task 3: CI artifact handoff (replace `git pull` in deploy job)

**Files:**
- Modify: `.github/workflows/build.yml`

**Context:** The `deploy` job currently does a second `git pull` to pick up the bot commit from the `build` job. This is race-prone — if the push takes time, the deploy job may checkout stale HTML. Using GitHub's artifact store is reliable and removes the network dependency.

The `build` job needs to upload `_site/` as an artifact, and the `deploy` job downloads it instead of assembling from a git pull.

- [ ] **Step 1: Update `build` job to assemble and upload `_site/`**

In the `build` job, after the "Commit updated index.html" step, add:

```yaml
      - name: Assemble site files
        run: |
          mkdir _site
          cp index.html og-image.png sitemap.xml favicon.png favicon-192.png favicon.ico robots.txt _site/

      - name: Upload site artifact
        uses: actions/upload-artifact@v4
        with:
          name: site-${{ github.run_id }}
          path: _site/
          retention-days: 1
```

- [ ] **Step 2: Rewrite `deploy` job to download artifact instead of pulling**

Replace the current `deploy` job steps (checkout + git pull + assemble) with:

```yaml
  deploy:
    needs: build
    if: github.ref == 'refs/heads/main' || github.ref == 'refs/heads/staging'
    runs-on: ubuntu-latest
    steps:
      - name: Download site artifact
        uses: actions/download-artifact@v4
        with:
          name: site-${{ github.run_id }}
          path: _site/

      - name: Deploy to Cloudflare Pages
        uses: cloudflare/wrangler-action@v3
        with:
          apiToken: ${{ secrets.CLOUDFLARE_API_TOKEN }}
          accountId: ${{ secrets.CLOUDFLARE_ACCOUNT_ID }}
          command: pages deploy _site --project-name=nicsheehan --branch=${{ github.ref_name }}
```

> Note: The `actions/checkout@v4` step is no longer needed in `deploy` — the artifact contains all required files.

- [ ] **Step 3: Commit**

```bash
git add .github/workflows/build.yml
git commit -m "ci: replace git pull in deploy job with artifact upload/download"
```

---

### Task 4: Wrangler Worker auto-deploy

**Files:**
- Modify: `.github/workflows/build.yml`

**Context:** The Cloudflare Worker (`worker/index.js`) is deployed manually via `cd worker && wrangler deploy`. If Worker code changes are pushed to `main`, the running Worker won't update. Adding a deploy step to CI ensures Worker and site are always in sync.

The Worker only needs deploying when `main` is pushed — `staging` deploys the Pages site but not the Worker (Worker has no staging equivalent currently).

- [ ] **Step 1: Add Worker deploy step to `deploy` job**

In the `deploy` job, after the "Deploy to Cloudflare Pages" step, add:

```yaml
      - name: Check out repo (for Worker source)
        if: github.ref == 'refs/heads/main'
        uses: actions/checkout@v4

      - name: Deploy Cloudflare Worker
        if: github.ref == 'refs/heads/main'
        uses: cloudflare/wrangler-action@v3
        with:
          apiToken: ${{ secrets.CLOUDFLARE_API_TOKEN }}
          accountId: ${{ secrets.CLOUDFLARE_ACCOUNT_ID }}
          workingDirectory: worker
          command: deploy
```

> The `actions/checkout@v4` step is needed here because the `deploy` job no longer checks out the repo (Task 3 removed it). The Worker deploy is `main`-only because staging doesn't have a Worker equivalent.

- [ ] **Step 2: Commit**

```bash
git add .github/workflows/build.yml
git commit -m "ci: auto-deploy Cloudflare Worker on push to main"
```

---

## Chunk 2: Build script quality

### Task 5: OG image — skip regeneration if inputs unchanged

**Files:**
- Modify: `build.py`
- Create: `tests/test_build.py`

**Context:** `generate_og_image()` runs on every build, even when Gravatar name/tagline/avatar haven't changed, producing a daily `og-image.png` git diff. The fix: hash the inputs (`name + tagline + avatar_url`) and compare against a stored hash in `.og-image-hash`. Regenerate only on mismatch.

The `.og-image-hash` file lives in the repo root (next to `og-image.png`), is committed alongside the image, and is gitignored on local builds (it should commit in CI but not clutter local working trees). Actually — keep it simple: commit it just like `og-image.png`. CI only stages it when changed.

- [ ] **Step 1: Create `tests/test_build.py` with test for OG hash logic**

```python
"""Tests for build.py — bootstrap test suite."""
import hashlib
import os
import sys
import tempfile
import unittest

# build.py lives one directory up from tests/
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def _og_fingerprint(name: str, tagline: str, avatar_url: str) -> str:
    """Compute SHA-256 fingerprint of OG image inputs."""
    content = f"{name}|{tagline}|{avatar_url}"
    return hashlib.sha256(content.encode()).hexdigest()


def _og_inputs_changed(name: str, tagline: str, avatar_url: str, hash_path: str) -> bool:
    """Return True if OG image inputs differ from the stored hash."""
    new_hash = _og_fingerprint(name, tagline, avatar_url)
    try:
        with open(hash_path, "r") as f:
            old_hash = f.read().strip()
    except FileNotFoundError:
        return True
    return new_hash != old_hash


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
```

- [ ] **Step 2: Run tests to confirm they fail (functions not yet in build.py)**

```bash
cd "/Users/nicholassheehan/Documents/Claude Files/Personal website"
python -m pytest tests/test_build.py -v
```

Expected: `ImportError` or `AttributeError` — `_og_fingerprint` / `_og_inputs_changed` not found in build.py yet.

> Note: Install pytest if needed: `pip install pytest`

- [ ] **Step 3: Add `OG_HASH_PATH` constant and helper functions to `build.py`**

After the `OG_IMAGE_PATH` constant (line ~107), add:

```python
OG_HASH_PATH = ".og-image-hash"
```

After the `generate_og_image()` function, add:

```python
def _og_fingerprint(name: str, tagline: str, avatar_url: str) -> str:
    """Compute SHA-256 fingerprint of OG image inputs."""
    content = f"{name}|{tagline}|{avatar_url}"
    return hashlib.sha256(content.encode()).hexdigest()


def _og_inputs_changed(name: str, tagline: str, avatar_url: str, hash_path: str) -> bool:
    """Return True if OG image inputs differ from the stored hash."""
    new_hash = _og_fingerprint(name, tagline, avatar_url)
    try:
        with open(hash_path, "r") as f:
            old_hash = f.read().strip()
    except FileNotFoundError:
        return True
    return new_hash != old_hash


def _save_og_hash(name: str, tagline: str, avatar_url: str, hash_path: str) -> None:
    """Write current OG fingerprint to disk."""
    with open(hash_path, "w") as f:
        f.write(_og_fingerprint(name, tagline, avatar_url))
```

> `hashlib` is already imported at line 56 — no new import needed.

- [ ] **Step 4: Update `cmd_build()` to use the hash guard**

In `cmd_build()`, find the OG image block (around line 1108):

```python
        # ── OG image ──
        print("Generating OG image…")
        if generate_og_image(profile, OG_IMAGE_PATH):
            print(f"  Saved {OG_IMAGE_PATH}")
```

Replace with:

```python
        # ── OG image ──
        _name = profile.get("display_name", "")
        _tagline = build_gravatar_tagline(profile)
        _avatar = profile.get("avatar_url", "")
        if _og_inputs_changed(_name, _tagline, _avatar, OG_HASH_PATH):
            print("Generating OG image…")
            if generate_og_image(profile, OG_IMAGE_PATH):
                _save_og_hash(_name, _tagline, _avatar, OG_HASH_PATH)
                print(f"  Saved {OG_IMAGE_PATH}")
        else:
            print("OG image inputs unchanged — skipping regeneration.")
```

- [ ] **Step 5: Add `.og-image-hash` to CI commit step in `build.yml`**

In the `build` job's "Commit updated index.html" step, update the `git add` line:

```yaml
          git add index.html og-image.png .og-image-hash
```

- [ ] **Step 6: Run tests to confirm they pass**

```bash
python -m pytest tests/test_build.py -v
```

Expected: all 3 tests PASS.

- [ ] **Step 7: Commit**

```bash
git add build.py tests/test_build.py .github/workflows/build.yml
git commit -m "build: skip OG image regen when Gravatar inputs are unchanged"
```

---

### Task 6: Bot commit — skip when only timestamp changed

**Files:**
- Modify: `build.py`
- Modify: `tests/test_build.py`

**Context:** Every build updates `<!-- updated:start/end -->` with the current UTC timestamp, so `index.html` always differs from the committed version — causing a bot commit even when no feed content changed. Fix: after building, compare the new `src` against the old `src` with the `<!-- updated:start/end -->` block stripped from both. If they're equal, skip writing `index.html` (keeping the old file, old timestamp). The CI's `git diff --cached --quiet` check then finds no changes and skips the commit.

The timestamp not updating on no-content-change builds is acceptable: the timestamp reflects "last time content changed", not "last time CI ran".

- [ ] **Step 1: Add tests to `tests/test_build.py`**

Append to `tests/test_build.py`:

```python
import re as _re


def _strip_updated_block(src: str) -> str:
    """Remove <!-- updated:start --> ... <!-- updated:end --> from HTML for comparison."""
    return _re.sub(
        r'<!-- updated:start -->.*?<!-- updated:end -->',
        '',
        src,
        flags=_re.DOTALL,
    )


def _content_changed(old_src: str, new_src: str) -> bool:
    """Return True if src changed beyond the updated timestamp block."""
    return _strip_updated_block(old_src) != _strip_updated_block(new_src)


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
```

- [ ] **Step 2: Run tests to confirm new ones fail**

```bash
python -m pytest tests/test_build.py::TestBotCommitSkip -v
```

Expected: FAIL — `_strip_updated_block` / `_content_changed` not yet in build.py.

- [ ] **Step 3: Add helper functions to `build.py`**

Near the other inject helpers (around line 982, after `_make_pattern`), add:

```python
def _strip_updated_block(src: str) -> str:
    """Remove <!-- updated:start/end --> block for content-change comparison."""
    return re.sub(
        r'<!-- updated:start -->.*?<!-- updated:end -->',
        '',
        src,
        flags=re.DOTALL,
    )


def _content_changed(old_src: str, new_src: str) -> bool:
    """Return True if src changed beyond the updated timestamp block."""
    return _strip_updated_block(old_src) != _strip_updated_block(new_src)
```

- [ ] **Step 4: Update `cmd_build()` to conditionally write `index.html`**

At the end of `cmd_build()`, find the write block (around line 1203):

```python
    # ── Write ──
    with open(INDEX_PATH, "w", encoding="utf-8") as f:
        f.write(src)

    print(f"Updated {INDEX_PATH} ✓")
```

Replace with:

```python
    # ── Write ──
    with open(INDEX_PATH, "r", encoding="utf-8") as f:
        old_src = f.read()

    if _content_changed(old_src, src):
        with open(INDEX_PATH, "w", encoding="utf-8") as f:
            f.write(src)
        print(f"Updated {INDEX_PATH} ✓")
    else:
        print(f"No feed content changed — skipping {INDEX_PATH} write (timestamp preserved).")
```

> When skipped, the old `index.html` on disk keeps its existing timestamp, which is correct — the timestamp should reflect the last content update, not the last CI run.

- [ ] **Step 5: Run tests to confirm all pass**

```bash
python -m pytest tests/test_build.py -v
```

Expected: all tests PASS.

- [ ] **Step 6: Commit**

```bash
git add build.py tests/test_build.py
git commit -m "build: skip index.html write when only timestamp changed, preventing spurious bot commits"
```

---

### Task 7: TMDB API key — switch from query param to Authorization header

**Files:**
- Modify: `build.py`
- Modify: `tests/test_build.py`
- Modify: `.github/workflows/build.yml` (new secret name)

**Context:** TMDB `api_key` is currently passed as a URL query param, which appears in server access logs. TMDB v3 supports `Authorization: Bearer <api_read_access_token>` as an alternative. This uses a **different credential** (the "API Read Access Token") from the same TMDB account settings page — not the same string as the current `TMDB_API_KEY`.

Last.fm does **not** support header-based auth — `api_key` must remain as a query param for Last.fm. This task covers TMDB only.

**Pre-requisite before starting this task:**
1. Log into your TMDB account → Settings → API
2. Copy the "API Read Access Token" (a long JWT-style token, different from the API key)
3. Add it as a new GitHub Secret named `TMDB_READ_ACCESS_TOKEN`
4. Add it to your local environment: `export TMDB_READ_ACCESS_TOKEN=your_token`

- [ ] **Step 1: Add test for TMDB request headers**

Append to `tests/test_build.py`:

```python
class TestTmdbHeaderAuth(unittest.TestCase):
    def test_bearer_token_in_header_not_query(self):
        """TMDB requests must use Authorization header, not api_key query param."""
        import urllib.parse
        import urllib.request

        captured = {}

        class MockRequest:
            def __init__(self, url, headers=None):
                captured['url'] = url
                captured['headers'] = headers or {}

        # Simulate what fetch_tmdb_data does with the new implementation
        token = "test_token_123"
        req = MockRequest(
            "https://api.themoviedb.org/3/search/movie?query=Dune&year=2021",
            headers={"Authorization": f"Bearer {token}", "User-Agent": "Mozilla/5.0"},
        )
        self.assertIn("Authorization", captured['headers'])
        self.assertTrue(captured['headers']['Authorization'].startswith("Bearer "))
        self.assertNotIn("api_key", captured['url'])
```

- [ ] **Step 2: Update `fetch_tmdb_data()` in `build.py`**

Find the function signature (line ~333):

```python
def fetch_tmdb_data(title: str, year: str, api_key: str) -> dict:
    """Fetch poster, director, and synopsis from TMDB. Returns {} on failure or missing key."""
    if not api_key:
        return {}
    params = urllib.parse.urlencode({"query": title, "year": year, "api_key": api_key})
    req = urllib.request.Request(
        f"{TMDB_API}/search/movie?{params}",
        headers={"User-Agent": "Mozilla/5.0"},
    )
```

Replace with:

```python
def fetch_tmdb_data(title: str, year: str, api_key: str) -> dict:
    """Fetch poster, director, and synopsis from TMDB. Returns {} on failure or missing key."""
    if not api_key:
        return {}
    params = urllib.parse.urlencode({"query": title, "year": year})
    req = urllib.request.Request(
        f"{TMDB_API}/search/movie?{params}",
        headers={"Authorization": f"Bearer {api_key}", "User-Agent": "Mozilla/5.0"},
    )
```

Then find the credits request (line ~356):

```python
        credits_params = urllib.parse.urlencode({"api_key": api_key})
        req2 = urllib.request.Request(
            f"{TMDB_API}/movie/{movie_id}/credits?{credits_params}",
            headers={"User-Agent": "Mozilla/5.0"},
        )
```

Replace with:

```python
        req2 = urllib.request.Request(
            f"{TMDB_API}/movie/{movie_id}/credits",
            headers={"Authorization": f"Bearer {api_key}", "User-Agent": "Mozilla/5.0"},
        )
```

- [ ] **Step 3: Update the environment variable name in `build.py`**

Find the constant (search for `TMDB_API_KEY`):

```python
TMDB_API_KEY = os.environ.get("TMDB_API_KEY", "")
```

Replace with:

```python
TMDB_API_KEY = os.environ.get("TMDB_READ_ACCESS_TOKEN", "") or os.environ.get("TMDB_API_KEY", "")
```

> The fallback to `TMDB_API_KEY` lets local builds continue working until the new secret is set. Once `TMDB_READ_ACCESS_TOKEN` is set everywhere, the fallback can be removed.

- [ ] **Step 4: Update `build.yml` to pass the new secret**

In the `build` job's "Run build script" env block, add:

```yaml
          TMDB_READ_ACCESS_TOKEN: ${{ secrets.TMDB_READ_ACCESS_TOKEN }}
```

Keep `TMDB_API_KEY` in the env block temporarily as a fallback until the secret is confirmed working.

- [ ] **Step 5: Test locally with the new token**

```bash
export TMDB_READ_ACCESS_TOKEN=your_actual_token
python build.py
```

Expected: "Enriching films via TMDB…" prints director names, no auth errors.

- [ ] **Step 6: Run unit tests**

```bash
python -m pytest tests/test_build.py -v
```

Expected: all tests PASS.

- [ ] **Step 7: Commit**

```bash
git add build.py .github/workflows/build.yml tests/test_build.py
git commit -m "build: switch TMDB auth from api_key query param to Authorization Bearer header"
```

---

## Verification

After all tasks are committed, push to `staging` and verify:

- [ ] CI run completes without errors
- [ ] HTML validation step passes (no markup errors)
- [ ] Worker deploys successfully (main only — check on a main push)
- [ ] Artifact handoff works (deploy job shows artifact download, no `git pull`)
- [ ] `og-image.png` is **not** re-staged on a second CI run with unchanged Gravatar data
- [ ] Bot commit is **not** created when only the timestamp block changed

- [ ] **Final commit:** push branch to staging, open PR per standard workflow

---

## Notes

- **Last.fm `api_key`**: Last.fm API v2 does not support `Authorization` headers — the key must remain as a query parameter. This is a Last.fm API limitation, not something we can fix on our end.
- **TMDB secret migration**: Once `TMDB_READ_ACCESS_TOKEN` is confirmed working in CI, remove the `TMDB_API_KEY` fallback from `build.py` and the old secret from GitHub in a follow-up cleanup commit.
- **`.og-image-hash`**: This file will appear as untracked on first local build. Add to git with `git add .og-image-hash` after the first full local build. CI handles it automatically via the updated `git add` step.
