# Iteration 1 — Housekeeping & Correctness Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Six pure correctness fixes to `build.py` and supporting files — no visual changes.

**Architecture:** All changes are in `build.py` (output generation) and `index.html` (static structure). No new files needed except the sitemap update (written by build). Each task is isolated; order doesn't matter except Task 6 (timestamp) builds on the updated format string.

**Tech Stack:** Python 3.9+ (tomli fallback), stdlib only, regex injection into `index.html`

---

### Task 1: Remove `twitter:*` meta tags from `build_meta_html()`

**Files:**
- Modify: `build.py:508-511` (the three `twitter:*` lines in `build_meta_html`)

**Step 1: Remove the three twitter lines**

In `build_meta_html()`, delete these three lines from the `lines` list:
```python
f'  <meta name="twitter:card" content="{html.escape(social["twitter_card"])}">',
f'  <meta name="twitter:title" content="{html.escape(site["title"])}">',
f'  <meta name="twitter:description" content="{html.escape(site["description"])}">',
```

**Step 2: Remove the `social["twitter_card"]` reference**

After removing those lines, `social` dict is no longer read in `build_meta_html` (only `og_type` was used from `social`, which stays). The function still uses `social["og_type"]` so keep the `social = config["social"]` line.

**Step 3: Verify**

Run build and confirm no `twitter:` tags in the output:
```bash
python3 build.py 2>&1 | head -5
grep "twitter:" index.html
```
Expected: `grep` returns nothing.

**Step 4: Commit**
```bash
git add build.py
git commit -m "Remove twitter:* meta tags (OG tags are sufficient)"
```

---

### Task 2: Update `build.py` docstring to reference `site.toml`

**Files:**
- Modify: `build.py:3-33` (the module docstring)

**Step 1: Update the docstring**

Replace the existing docstring with:
```python
"""
Build script for nicsheehan.com

Fetches data from five sources and writes them into index.html:
  1. site.toml — site metadata, analytics, and data source config
  2. Gravatar profile (via REST API — GRAVATAR_API_KEY env var for full data)
  3. Goodreads "currently reading" and "read" shelves (via RSS — no auth needed)
  4. Letterboxd recently watched films (via RSS — no auth needed)
  5. Instapaper starred/liked articles (via API — OAuth 1.0a)

Usage:
    python build.py              # full build
    python build.py auth         # one-time: exchange Instapaper credentials for OAuth tokens

Setup — site.toml:
    Edit site.toml to set title, description, URL, analytics ID, and feed URLs.

Setup — Gravatar:
    Set GRAVATAR_USERNAME in site.toml (sources.gravatar.username).
    Pulls display_name, job_title, company, location, and description.
    Set GRAVATAR_API_KEY env var for links and contact info (unauthenticated gives basic profile only).

Setup — Goodreads:
    Set sources.goodreads.currently_reading_rss and read_rss in site.toml.
    Find your RSS URLs at: goodreads.com → My Books → shelf → RSS link

Setup — Letterboxd:
    Set sources.letterboxd.rss in site.toml.
    Find it at: letterboxd.com → your profile → RSS link

Setup — Instapaper:
    1. Request API credentials at https://www.instapaper.com/main/request_oauth_consumer_token
    2. Set INSTAPAPER_CONSUMER_KEY and INSTAPAPER_CONSUMER_SECRET as env vars
    3. Run:  python build.py auth
       This exchanges your username/password for OAuth tokens (stored in .instapaper_tokens)
       You only need to do this once.
    For CI, set all four INSTAPAPER_* values as environment variables/secrets.
"""
```

**Step 2: Verify**

```bash
python3 -c "import build; help(build)" 2>&1 | head -10
```
Expected: updated docstring appears.

**Step 3: Commit**
```bash
git add build.py
git commit -m "Update build.py docstring to reference site.toml"
```

---

### Task 3: Fix JSON-LD duplicate `sameAs` URLs (normalize trailing slashes)

**Files:**
- Modify: `build.py:234-240` (the `same_as` construction in `build_jsonld()`)

**Step 1: Add a normalizer and use it**

Replace the `same_as` construction block (from `same_as = [profile["profile_url"]]` through `data["sameAs"] = same_as`) with:

```python
def _norm_url(url: str) -> str:
    """Strip trailing slash for deduplication purposes."""
    return url.rstrip("/")

same_as_seen = set()
same_as = []

def _add_url(url: str):
    key = _norm_url(url)
    if key not in same_as_seen:
        same_as_seen.add(key)
        same_as.append(url)

_add_url(profile["profile_url"])
for link in profile.get("links", []):
    if link.get("url"):
        _add_url(link["url"])
for acct in profile.get("verified_accounts", []):
    if acct.get("url"):
        _add_url(acct["url"])

data["sameAs"] = same_as
```

Note: define `_norm_url` as a module-level helper (above `build_jsonld`), not inside it. The inner functions (`_add_url`, `same_as_seen`, `same_as`) stay local to `build_jsonld`.

**Step 2: Verify**

Run a quick sanity check — if you have `GRAVATAR_API_KEY` available:
```bash
python3 -c "
import build, json
p = build.fetch_gravatar(build.GRAVATAR_USERNAME, build.GRAVATAR_API_KEY)
j = json.loads(build.build_jsonld(p, build.SITE_URL))
urls = j.get('sameAs', [])
normalized = [u.rstrip('/') for u in urls]
assert len(normalized) == len(set(normalized)), 'Duplicates found!'
print('OK — no duplicates, count:', len(urls))
"
```
Expected: `OK — no duplicates, count: N`

**Step 3: Commit**
```bash
git add build.py
git commit -m "Fix JSON-LD sameAs duplicate URLs via trailing-slash normalisation"
```

---

### Task 4: Inject `<html lang>` from `site.toml`

**Files:**
- Modify: `build.py` — add lang injection step in `cmd_build()`
- Modify: `index.html` — `<html lang="en-AU">` stays as-is (default until build runs)

**Step 1: Add a direct regex replace in `cmd_build()`**

Add this block near the top of `cmd_build()`, right after reading `src` from file (before the meta injection):

```python
# ── <html lang> (from site.toml) ──
lang = CONFIG["site"].get("lang", "en")
src = re.sub(r'<html\b[^>]*>', f'<html lang="{html.escape(lang)}">', src, count=1)
print(f"Injecting lang={lang}…")
```

No comment markers needed — it's a direct attribute replace on the `<html>` tag.

**Step 2: Verify**

```bash
python3 build.py 2>&1 | grep "lang="
grep "<html" index.html
```
Expected: `<html lang="en-AU">` in output.

**Step 3: Commit**
```bash
git add build.py
git commit -m "Inject <html lang> from site.toml lang field"
```

---

### Task 5: Update `sitemap.xml` `<lastmod>` on each build

**Files:**
- Modify: `build.py` — add `update_sitemap()` function and call it in `cmd_build()`
- Modify: `sitemap.xml` — add `<lastmod>` element (will be updated by build)

**Step 1: Add `SITEMAP_PATH` constant**

Near the other path constants (around line 80):
```python
SITEMAP_PATH = "sitemap.xml"
```

**Step 2: Add `update_sitemap()` function**

Add after the `inject()` function (before the CLI section):
```python
def update_sitemap(path: str, last_mod: datetime):
    """Write lastmod date into sitemap.xml."""
    lastmod_str = last_mod.strftime("%Y-%m-%d")
    content = f"""<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url>
    <loc>{SITE_URL}/</loc>
    <lastmod>{lastmod_str}</lastmod>
    <changefreq>daily</changefreq>
  </url>
</urlset>
"""
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"  Updated {path} with lastmod {lastmod_str}")
```

**Step 3: Call it in `cmd_build()`**

After the `# ── Last updated timestamp ──` block (near the end of `cmd_build()`), add:
```python
# ── Sitemap ──
update_sitemap(SITEMAP_PATH, now)
```

(`now` is already defined earlier in `cmd_build()` as `datetime.now(timezone.utc)`)

**Step 4: Verify**

```bash
python3 build.py 2>&1 | grep sitemap
cat sitemap.xml
```
Expected: `sitemap.xml` contains a `<lastmod>` with today's date in `YYYY-MM-DD` format.

**Step 5: Commit**
```bash
git add build.py sitemap.xml
git commit -m "Update sitemap.xml <lastmod> on each build"
```

---

### Task 6: Update timestamp format to "Last built DD Mon YYYY at HH:MM UTC"

**Files:**
- Modify: `build.py:667-670` (the timestamp block in `cmd_build()`)

**Step 1: Update the format string and HTML**

Replace:
```python
updated_str = now.strftime("%-d %b %Y")
updated_html = f'        <p class="updated">Last updated {updated_str}</p>'
```

With:
```python
updated_str = now.strftime("%-d %b %Y at %H:%M UTC")
updated_html = f'        <p class="updated">Last built {updated_str}</p>'
```

**Step 2: Verify**

```bash
python3 build.py 2>&1 | grep Timestamp
grep "Last built" index.html
```
Expected: something like `Last built 19 Feb 2026 at 22:00 UTC`

**Step 3: Commit**
```bash
git add build.py
git commit -m "Update timestamp format to 'Last built D Mon YYYY at HH:MM UTC'"
```

---

### Final: push

```bash
git pull --rebase origin main
git push origin main
```
