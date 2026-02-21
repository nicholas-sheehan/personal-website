# Music — Last.fm Integration Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add a "Listening to lately" section to the site that shows the user's top 8 tracks of the current month, pulled from Last.fm at build time.

**Architecture:** Follows the exact same pattern as Letterboxd — a fetch function, a build-html function, a regex pattern, and a call in `cmd_build()`. Config goes in `site.toml` (username + limit), the API key goes in an env var / GitHub secret. The music section is added to the existing `.content-grid` in `index.html` as a peer section; grid layout restructuring happens in iteration 4.

**Tech Stack:** Python 3.9+, `urllib.request` (stdlib only — no new dependencies), Last.fm REST API (JSON), `LASTFM_API_KEY` env var.

---

## Prerequisites (manual, before starting)

1. **Get a Last.fm API key:**
   - Go to https://www.last.fm/api/account/create
   - App name: "nicsheehan personal site" (or similar)
   - Copy the **API key** (not the shared secret — you don't need that)

2. **Find your Last.fm username:**
   - Log in at last.fm → your profile URL is `last.fm/user/<username>`

3. **Add the GitHub secret:**
   - Repo → Settings → Secrets and variables → Actions → New repository secret
   - Name: `LASTFM_API_KEY`, value: the API key from step 1

---

### Task 1: Add `[sources.lastfm]` to `site.toml`

**Files:**
- Modify: `site.toml`

**Step 1: Add the block**

Append to the end of `site.toml`:

```toml
[sources.lastfm]
username = "YOUR_LASTFM_USERNAME"  # replace with your Last.fm username
limit = 8
```

**Step 2: Verify it parses**

```bash
python3 -c "
try:
    import tomllib
except ModuleNotFoundError:
    import tomli as tomllib
with open('site.toml', 'rb') as f:
    c = tomllib.load(f)
print(c['sources']['lastfm'])
"
```

Expected: `{'username': 'YOUR_LASTFM_USERNAME', 'limit': 8}`

**Step 3: Commit**

```bash
git add site.toml
git commit -m "Add Last.fm config to site.toml"
```

---

### Task 2: Add Last.fm constants to `build.py`

**Files:**
- Modify: `build.py` — constants block (around line 86, after `INSTAPAPER_LIMIT`)

**Step 1: Add constants**

After the `INSTAPAPER_LIMIT` line, add:

```python
LASTFM_USERNAME = CONFIG["sources"]["lastfm"]["username"]
LASTFM_API_KEY = os.environ.get("LASTFM_API_KEY", "")
LASTFM_LIMIT = CONFIG["sources"]["lastfm"]["limit"]
```

**Step 2: Verify**

```bash
python3 -c "import build; print(build.LASTFM_USERNAME, build.LASTFM_LIMIT)"
```

Expected: `YOUR_LASTFM_USERNAME 8`

**Step 3: Commit**

```bash
git add build.py
git commit -m "Add Last.fm constants to build.py"
```

---

### Task 3: Add `fetch_lastfm_top_tracks()` to `build.py`

**Files:**
- Modify: `build.py` — add after the Instapaper section, before the Meta & analytics section (around line 529)

**Step 1: Add the fetch function**

Add a new section block after the Instapaper section:

```python
# ══════════════════════════════════════════════════════════════════
#  Last.fm (REST API)
# ══════════════════════════════════════════════════════════════════

LASTFM_API = "https://ws.audioscrobbler.com/2.0/"


def fetch_lastfm_top_tracks(username: str, api_key: str, limit: int) -> list[dict]:
    """Return a list of {title, artist, plays} dicts from Last.fm top tracks."""
    params = urllib.parse.urlencode({
        "method": "user.getTopTracks",
        "user": username,
        "period": "1month",
        "limit": str(limit),
        "api_key": api_key,
        "format": "json",
    })
    url = f"{LASTFM_API}?{params}"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=15) as resp:
        data = json.loads(resp.read().decode())

    tracks = []
    for track in data.get("toptracks", {}).get("track", []):
        tracks.append({
            "title": track.get("name", ""),
            "artist": track.get("artist", {}).get("name", ""),
            "plays": int(track.get("playcount", 0)),
        })
    return tracks
```

**Step 2: Smoke-test the fetch (requires API key)**

```bash
LASTFM_API_KEY="your_key_here" python3 -c "
import build
tracks = build.fetch_lastfm_top_tracks(build.LASTFM_USERNAME, build.LASTFM_API_KEY, 3)
for t in tracks:
    print(t)
"
```

Expected: 3 dicts like `{'title': '...', 'artist': '...', 'plays': N}`

**Step 3: Commit**

```bash
git add build.py
git commit -m "Add fetch_lastfm_top_tracks() to build.py"
```

---

### Task 4: Add `build_music_html()` and `MUSIC_PATTERN` to `build.py`

**Files:**
- Modify: `build.py`
  - Add `build_music_html()` after `fetch_lastfm_top_tracks()`
  - Add `MUSIC_PATTERN` in the patterns block (around line 581)

**Step 1: Add `build_music_html()`**

Add directly after `fetch_lastfm_top_tracks()`:

```python
def build_music_html(tracks: list[dict]) -> str:
    """Turn a list of tracks into <li> elements."""
    if not tracks:
        return "          <li>Nothing at the moment — check back soon.</li>"
    lines = []
    for track in tracks:
        t = html.escape(track["title"])
        a = html.escape(track["artist"])
        p = track["plays"]
        play_word = "play" if p == 1 else "plays"
        lines.append(
            f'          <li class="track">'
            f'<span class="track-title">{t}</span>'
            f'<span class="track-meta">{a} · {p} {play_word}</span>'
            f'</li>'
        )
    return "\n".join(lines)
```

**Step 2: Add `MUSIC_PATTERN`**

In the patterns block (after `INSTAPAPER_PATTERN`), add:

```python
MUSIC_PATTERN = _make_pattern("music")
```

**Step 3: Test `build_music_html()` in isolation**

```bash
python3 -c "
import build
tracks = [
    {'title': 'Paranoid Android', 'artist': 'Radiohead', 'plays': 23},
    {'title': 'Fake Plastic Trees', 'artist': 'Radiohead', 'plays': 1},
]
print(build.build_music_html(tracks))
print('---')
print(build.build_music_html([]))
"
```

Expected output:
```
          <li class="track"><span class="track-title">Paranoid Android</span><span class="track-meta">Radiohead · 23 plays</span></li>
          <li class="track"><span class="track-title">Fake Plastic Trees</span><span class="track-meta">Radiohead · 1 play</span></li>
---
          <li>Nothing at the moment — check back soon.</li>
```

Note: "1 play" (singular), "23 plays" (plural) — verify this is correct.

**Step 4: Commit**

```bash
git add build.py
git commit -m "Add build_music_html() and MUSIC_PATTERN to build.py"
```

---

### Task 5: Wire Last.fm into `cmd_build()`

**Files:**
- Modify: `build.py` — `cmd_build()` and the module docstring

**Step 1: Add the fetch + inject block to `cmd_build()`**

After the Instapaper block (after the `except` clause around line 727), add:

```python
    # ── Last.fm ──
    if not LASTFM_API_KEY:
        print("⚠  Skipping Last.fm — set LASTFM_API_KEY env var first.")
    else:
        print("Fetching Last.fm top tracks…")
        try:
            tracks = fetch_lastfm_top_tracks(LASTFM_USERNAME, LASTFM_API_KEY, LASTFM_LIMIT)
            print(f"  Found {len(tracks)} top track(s).")
            src = inject(src, MUSIC_PATTERN, build_music_html(tracks), "music")
        except Exception as e:
            print(f"  ⚠  Last.fm fetch failed: {e} — keeping existing content")
```

**Step 2: Update the module docstring**

At the top of `build.py`, update the sources list in the docstring to include Last.fm:

Change:
```
Fetches data from five sources and writes them into index.html:
  1. site.toml — site metadata, analytics, and data source config
  2. Gravatar profile (via REST API — GRAVATAR_API_KEY env var for full data)
  3. Goodreads "currently reading" and "read" shelves (via RSS — no auth needed)
  4. Letterboxd recently watched films (via RSS — no auth needed)
  5. Instapaper starred/liked articles (via API — OAuth 1.0a)
```

To:
```
Fetches data from six sources and writes them into index.html:
  1. site.toml — site metadata, analytics, and data source config
  2. Gravatar profile (via REST API — GRAVATAR_API_KEY env var for full data)
  3. Goodreads "currently reading" and "read" shelves (via RSS — no auth needed)
  4. Letterboxd recently watched films (via RSS — no auth needed)
  5. Instapaper starred/liked articles (via API — OAuth 1.0a)
  6. Last.fm top tracks this month (via REST API — LASTFM_API_KEY env var)
```

Also add a setup block for Last.fm after the Instapaper setup block:

```
Setup — Last.fm:
    Set sources.lastfm.username in site.toml to your Last.fm username.
    Set LASTFM_API_KEY env var (get one at last.fm/api/account/create).
```

**Step 3: Commit**

```bash
git add build.py
git commit -m "Wire Last.fm fetch into cmd_build()"
```

---

### Task 6: Add music section to `index.html`

**Files:**
- Modify: `index.html` — add music section inside `.content-grid`

**Step 1: Find the insertion point**

The `.content-grid` div ends with the Instapaper section closing `</section>` tag, then `</div>`. Add the music section after the Instapaper section, before `</div>`.

Locate this in `index.html`:
```html
        </section>
      </div>

      <nav class="links"
```

The `</section>` before `</div>` is the end of the Instapaper section.

**Step 2: Add the music section**

Insert before `      </div>` (the closing tag of `.content-grid`):

```html
        <section class="reading">
          <h2>Listening to lately</h2>
          <ul>
<!-- music:start -->
          <li>Nothing at the moment — check back soon.</li>
<!-- music:end -->
          </ul>
        </section>
```

**Step 3: Verify markers are correctly placed**

```bash
python3 -c "
import re, build
with open('index.html') as f:
    src = f.read()
m = build.MUSIC_PATTERN.search(src)
print('Found:', m is not None)
"
```

Expected: `Found: True`

**Step 4: Commit**

```bash
git add index.html
git commit -m "Add music section with markers to index.html"
```

---

### Task 7: Add CSS for track items to `style.css`

**Files:**
- Modify: `style.css` — add `.track-title` and `.track-meta` styles after the `.reading` block

**Step 1: Add styles**

After the `.reading a:focus-visible` block (end of the reading sections CSS block), add:

```css
/* --- Music tracks --- */

.reading li.track {
  display: flex;
  flex-direction: column;
  gap: 0.15rem;
}

.track-title {
  color: var(--text-primary);
}

.track-meta {
  font-family: var(--font-mono);
  font-size: 0.75rem;
  color: var(--text-tertiary);
}
```

**Step 2: Run a full build to inline the updated CSS**

```bash
LASTFM_API_KEY="your_key_here" python3 build.py
```

Expected: build completes, prints "Found N top track(s)."

**Step 3: Open `index.html` in a browser**

Verify:
- "Listening to lately" section appears in the grid
- Each track shows title on one line, "Artist · N plays" below in smaller mono text
- Spacing matches other sections

**Step 4: Commit**

```bash
git add style.css
git commit -m "Add CSS for track items (.track-title, .track-meta)"
```

---

### Task 8: Update the GitHub Actions workflow

**Files:**
- Modify: `.github/workflows/build.yml` — add `LASTFM_API_KEY` to the env block

**Step 1: Find the env block**

In `build.yml`, locate the `env:` block under the build step (where `GRAVATAR_API_KEY` and the Instapaper secrets are set).

**Step 2: Add the new secret**

Add alongside the existing secrets:

```yaml
LASTFM_API_KEY: ${{ secrets.LASTFM_API_KEY }}
```

**Step 3: Verify the secret is in GitHub**

Check that `LASTFM_API_KEY` was added to repo → Settings → Secrets and variables → Actions (done in prerequisites). The workflow will fail silently (skip Last.fm with a warning) if the secret is missing — it won't crash the build.

**Step 4: Commit**

```bash
git add .github/workflows/build.yml
git commit -m "Add LASTFM_API_KEY to GitHub Actions workflow"
```

---

### Task 9: Update roadmap

**Files:**
- Modify: `.claude/roadmap.md`

**Step 1: Update iteration 4**

Add "Music section" to the iteration 4 checklist:

```markdown
## Iteration 4 — Layout restructure
The big visual change. These are interdependent and ship together.

- [x] Music data pipeline (Last.fm fetch, build_music_html, markers, CSS)
- [ ] Content-aware grid redesigned with all four sections: books, films, music, articles
- [ ] "Currently reading" callout (extract from grid, prose format between bio and grid)
- [ ] Tighten list item density — `line-height: 1.5` and `padding: 0.4rem` on `.reading li`
```

**Step 2: Commit**

```bash
git add .claude/roadmap.md
git commit -m "Update roadmap: music pipeline done, grid TBD in iteration 4"
```

---

### Final: push

```bash
git restore index.html og-image.png sitemap.xml   # discard build artifacts
git pull --rebase origin main
git push origin main
```

Verify the Actions run completes and "Listening to lately" appears on the live site.
