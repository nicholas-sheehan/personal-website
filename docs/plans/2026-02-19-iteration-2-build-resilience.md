# Iteration 2 — Build Resilience & CI Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Make the build pipeline more robust and efficient — surviving network failures gracefully, caching deps, deploying only the right files, and cleaning Instapaper URLs.

**Architecture:** Four independent changes: (1) try/except guards around each external fetch in `build.py` so a failure keeps existing `index.html` content rather than crashing; (2) `requirements.txt` + pip cache in the GitHub Actions workflow; (3) `_site/` assembly in the deploy job so only HTML/CSS/images/CNAME hit GitHub Pages, not Python files; (4) a URL-cleaning helper that strips tracking query params from Instapaper bookmarks before they're rendered.

**Tech Stack:** Python 3.12 (CI) / 3.9+ (local), `urllib.parse` (stdlib), GitHub Actions (`actions/setup-python@v5` caching, `actions/upload-pages-artifact@v3`)

---

### Task 1: Resilient builds — wrap each feed fetch in try/except

**Files:**
- Modify: `build.py` — `cmd_build()` (lines ~636–698)

**Background:** Currently any network error (timeout, DNS failure, HTTP 5xx) crashes the entire build and leaves `index.html` unchanged. The fix: wrap each fetch block in `try/except Exception`, print a warning on failure, and skip the `inject()` call — so the existing content between the markers survives intact.

There are four fetch blocks to wrap: Gravatar, Goodreads, Letterboxd, Instapaper.

**Step 1: Wrap the Gravatar block**

Find this block in `cmd_build()` (starts around line 636):
```python
    # ── Gravatar ──
    print("Fetching Gravatar profile…")
    profile = fetch_gravatar(GRAVATAR_USERNAME, GRAVATAR_API_KEY)
    name = html.escape(profile.get("display_name", ""))
    ...
    print(f"  Name: {name}, tagline: {tagline}, links: {len(profile.get('links', []))}")

    # ── OG image ──
    print("Generating OG image…")
    if generate_og_image(profile, OG_IMAGE_PATH):
        print(f"  Saved {OG_IMAGE_PATH}")
```

Wrap the entire Gravatar + OG image block (everything from `print("Fetching Gravatar…")` through the OG image lines) in a try/except:

```python
    # ── Gravatar ──
    print("Fetching Gravatar profile…")
    try:
        profile = fetch_gravatar(GRAVATAR_USERNAME, GRAVATAR_API_KEY)
        name = html.escape(profile.get("display_name", ""))
        tagline = html.escape(build_gravatar_tagline(profile))
        bio = profile.get("description", "")
        avatar_url = profile.get("avatar_url", "")
        if avatar_url:
            avatar_html = f'        <img class="avatar" src="{html.escape(avatar_url)}?s=192" alt="{name}" width="96" height="96">'
            src = inject(src, GRAVATAR_AVATAR_PATTERN, avatar_html, "gravatar-avatar")
        if name:
            src = inject(src, GRAVATAR_NAME_PATTERN, f"        {name}", "gravatar-name")
        if tagline:
            src = inject(src, GRAVATAR_TAGLINE_PATTERN, f"        {tagline}", "gravatar-tagline")
        if bio:
            bio_html = f"        <p>{html.escape(bio)}</p>"
            src = inject(src, GRAVATAR_BIO_PATTERN, bio_html, "gravatar-bio")
        contact_email = profile.get("contact_info", {}).get("email", "")
        links_html = build_gravatar_links_html(profile, email=contact_email)
        if links_html:
            src = inject(src, GRAVATAR_LINKS_PATTERN, links_html, "gravatar-links")
        jsonld = build_jsonld(profile, SITE_URL)
        src = inject(src, JSONLD_PATTERN, f"    <script type=\"application/ld+json\">\n{jsonld}\n    </script>", "jsonld")
        print(f"  Name: {name}, tagline: {tagline}, links: {len(profile.get('links', []))}")

        # ── OG image ──
        print("Generating OG image…")
        if generate_og_image(profile, OG_IMAGE_PATH):
            print(f"  Saved {OG_IMAGE_PATH}")
    except Exception as e:
        print(f"  ⚠  Gravatar fetch failed: {e} — keeping existing content")
```

**Step 2: Wrap the Goodreads block**

Find the existing Goodreads section (starts around line 666):
```python
    # ── Goodreads ──
    if "YOUR_USER_ID" in GOODREADS_RSS:
        print("⚠  Skipping Goodreads — update sources.goodreads in site.toml first.")
    else:
        print("Fetching Goodreads RSS…")
        books = fetch_goodreads(GOODREADS_RSS)
        ...
```

Wrap the `else` body in try/except:
```python
    # ── Goodreads ──
    if "YOUR_USER_ID" in GOODREADS_RSS:
        print("⚠  Skipping Goodreads — update sources.goodreads in site.toml first.")
    else:
        print("Fetching Goodreads RSS…")
        try:
            books = fetch_goodreads(GOODREADS_RSS)
            print(f"  Found {len(books)} book(s) on currently-reading shelf.")
            src = inject(src, GOODREADS_PATTERN, build_book_html(books), "goodreads")

            print("Fetching Goodreads read shelf…")
            read_books = fetch_goodreads(GOODREADS_READ_RSS, limit=GOODREADS_READ_LIMIT)
            print(f"  Found {len(read_books)} book(s) on read shelf.")
            src = inject(src, GOODREADS_READ_PATTERN, build_book_html(read_books), "goodreads-read")
        except Exception as e:
            print(f"  ⚠  Goodreads fetch failed: {e} — keeping existing content")
```

**Step 3: Wrap the Letterboxd block**

Same pattern for Letterboxd:
```python
    # ── Letterboxd ──
    if "YOUR_USERNAME" in LETTERBOXD_RSS:
        print("⚠  Skipping Letterboxd — update sources.letterboxd in site.toml first.")
    else:
        print("Fetching Letterboxd RSS…")
        try:
            films = fetch_letterboxd(LETTERBOXD_RSS, LETTERBOXD_LIMIT)
            print(f"  Found {len(films)} recent film(s).")
            src = inject(src, LETTERBOXD_PATTERN, build_film_html(films), "letterboxd")
        except Exception as e:
            print(f"  ⚠  Letterboxd fetch failed: {e} — keeping existing content")
```

**Step 4: Wrap the Instapaper block**

```python
    # ── Instapaper ──
    tokens = load_tokens()
    if INSTAPAPER_CONSUMER_KEY == "YOUR_CONSUMER_KEY":
        print("⚠  Skipping Instapaper — set INSTAPAPER_CONSUMER_KEY env var first.")
    elif tokens is None:
        print("⚠  Skipping Instapaper — run 'python build.py auth' first.")
    else:
        print("Fetching Instapaper starred articles…")
        try:
            articles = fetch_instapaper_starred(tokens)
            print(f"  Found {len(articles)} starred article(s).")
            src = inject(src, INSTAPAPER_PATTERN, build_article_html(articles), "instapaper")
        except Exception as e:
            print(f"  ⚠  Instapaper fetch failed: {e} — keeping existing content")
```

**Step 5: Parse check**

```bash
python3 -c "import ast; ast.parse(open('build.py').read()); print('OK')"
```
Expected: `OK`

**Step 6: Commit**
```bash
git add build.py
git commit -m "Wrap feed fetches in try/except — keep existing content on failure"
```

---

### Task 2: Cache pip install (Pillow) in CI

**Files:**
- Create: `requirements.txt`
- Modify: `.github/workflows/build.yml`

**Step 1: Create `requirements.txt`**

```
Pillow
tomli; python_version < "3.11"
```

(Both packages `build.py` uses. `tomli` is only needed on Python < 3.11 — CI uses 3.12 which has `tomllib` built-in, so this line is effectively a no-op in CI but useful for local dev on Python 3.9/3.10.)

**Step 2: Update the workflow**

In `.github/workflows/build.yml`, find the `actions/setup-python@v5` step and add `cache: 'pip'`:

```yaml
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
          cache: 'pip'
```

Change the "Install dependencies" step to use `requirements.txt`:

```yaml
      - name: Install dependencies
        run: pip install -r requirements.txt
```

**Step 3: Verify workflow parses as valid YAML**

```bash
python3 -c "import yaml; yaml.safe_load(open('.github/workflows/build.yml')); print('OK')" 2>/dev/null || python3 -c "
import re
content = open('.github/workflows/build.yml').read()
assert 'cache:' in content
assert 'requirements.txt' in content
print('OK — cache and requirements.txt present')
"
```

**Step 4: Commit**
```bash
git add requirements.txt .github/workflows/build.yml
git commit -m "Cache pip deps and add requirements.txt"
```

---

### Task 3: Deploy only site files to Pages (`_site/` dir)

**Files:**
- Modify: `.github/workflows/build.yml` — deploy job
- Modify: `.gitignore` — add `_site/`

**Background:** The deploy job currently uploads `path: "."` to GitHub Pages, which deploys the entire repo — Python source, workflow files, TOML config, plan docs, etc. The fix is to copy only the needed site files into a `_site/` directory and upload that instead.

Files that belong on the site: `index.html`, `og-image.png`, `sitemap.xml`, `CNAME`, `favicon.png`, `favicon-192.png`.

**Step 1: Add `_site/` to `.gitignore`**

Check if `.gitignore` exists. If so, add `_site/` to it. If not, create it with just `_site/`. Read it first, then add the line.

**Step 2: Update the deploy job in `build.yml`**

In the `deploy:` job, find these steps:
```yaml
      - name: Pull latest (includes build commit)
        run: git pull origin main

      - uses: actions/configure-pages@v4

      - uses: actions/upload-pages-artifact@v3
        with:
          path: "."
```

Replace with:
```yaml
      - name: Pull latest (includes build commit)
        run: git pull origin main

      - name: Assemble site files
        run: |
          mkdir _site
          cp index.html og-image.png sitemap.xml CNAME favicon.png favicon-192.png _site/

      - uses: actions/configure-pages@v4

      - uses: actions/upload-pages-artifact@v3
        with:
          path: "_site"
```

**Step 3: Verify**

```bash
python3 -c "
content = open('.github/workflows/build.yml').read()
assert 'path: \"_site\"' in content or \"path: '_site'\" in content, 'path not updated'
assert 'mkdir _site' in content, 'mkdir step missing'
print('OK')
"
```

Also check `.gitignore` contains `_site/`:
```bash
grep "_site" .gitignore
```

**Step 4: Commit**
```bash
git add .github/workflows/build.yml .gitignore
git commit -m "Deploy only site files to Pages via _site/ assembly step"
```

---

### Task 4: Strip URL tracking params from Instapaper links

**Files:**
- Modify: `build.py` — add `_TRACKING_PARAMS` constant and `_strip_tracking_params()` function, update `fetch_instapaper_starred()`

**Background:** Instapaper sometimes saves URLs with tracking parameters (`utm_source`, `fbclid`, etc.) attached. These are noise — they inflate URLs displayed on the site and link to the same content as the clean URL.

**Step 1: Add the constant and helper function**

Add this block just above `fetch_instapaper_starred()` (around line 468):

```python
_TRACKING_PARAMS = frozenset({
    "utm_source", "utm_medium", "utm_campaign", "utm_content", "utm_term", "utm_id",
    "fbclid", "gclid", "mc_cid", "mc_eid",
})


def _strip_tracking_params(url: str) -> str:
    """Remove common URL tracking parameters from a URL."""
    parsed = urllib.parse.urlparse(url)
    qs = urllib.parse.parse_qs(parsed.query, keep_blank_values=True)
    clean_qs = {k: v for k, v in qs.items() if k.lower() not in _TRACKING_PARAMS}
    clean_query = urllib.parse.urlencode(clean_qs, doseq=True)
    return urllib.parse.urlunparse(parsed._replace(query=clean_query))
```

**Step 2: Call it in `fetch_instapaper_starred()`**

Find these lines inside `fetch_instapaper_starred()`:
```python
        articles.append({
            "title": item.get("title", "Untitled"),
            "url": item.get("url", "#"),
        })
```

Replace with:
```python
        articles.append({
            "title": item.get("title", "Untitled"),
            "url": _strip_tracking_params(item.get("url", "#")),
        })
```

**Step 3: Parse check + logic test**

```bash
python3 -c "
import build

# Test: tracking params stripped
url = 'https://example.com/article?utm_source=newsletter&utm_medium=email&id=123'
result = build._strip_tracking_params(url)
assert 'utm_source' not in result, f'utm_source not stripped: {result}'
assert 'utm_medium' not in result, f'utm_medium not stripped: {result}'
assert 'id=123' in result, f'id param incorrectly stripped: {result}'
print('OK:', result)

# Test: URL with no params is unchanged
url2 = 'https://example.com/article'
assert build._strip_tracking_params(url2) == url2
print('OK: no-param URL unchanged')

# Test: URL with only tracking params — query string becomes empty
url3 = 'https://example.com/?fbclid=abc123'
result3 = build._strip_tracking_params(url3)
assert 'fbclid' not in result3, f'fbclid not stripped: {result3}'
print('OK: all-tracking URL cleaned:', result3)
"
```
Expected: three `OK` lines.

**Step 4: Commit**
```bash
git add build.py
git commit -m "Strip URL tracking params from Instapaper links"
```

---

### Final: push

```bash
git pull --rebase origin main
git push origin main
```
