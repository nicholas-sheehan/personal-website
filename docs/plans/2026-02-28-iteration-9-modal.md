# Iteration 9 — Item Detail Modal: Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add click-to-expand detail modals to all four content panels (books, films, music, articles), showing richer data fetched at build time, with a "View on [Service] →" link inside each modal.

**Architecture:** `build.py` injects richer data as `data-*` attrs on `.panel-row` elements at build time. A single static modal element in `index.html` (placed before `</body>`, outside any injected markers) is populated and shown/hidden by a new inline `<script>` block. All four content types covered; TMDB provides film posters and director data; Last.fm `track.getInfo` / `artist.getInfo` provide album and bio.

**Tech Stack:** Python (build.py), vanilla JS (inline script), CSS (style.css). New API: TMDB (free account required).

**Design reference:** `docs/plans/2026-02-28-iteration-9-design.md`

---

## Before You Start

1. Sign up for a free TMDB account at https://www.themoviedb.org/signup and create an API key (Settings → API → Create). Copy the **API Key (v3 auth)** string.
2. Add `TMDB_API_KEY` to GitHub repo secrets (Settings → Secrets → Actions → New repository secret).
3. Have all existing env vars set locally for testing:
   ```bash
   GRAVATAR_API_KEY="..." INSTAPAPER_CONSUMER_KEY="..." INSTAPAPER_CONSUMER_SECRET="..." \
   INSTAPAPER_OAUTH_TOKEN="..." INSTAPAPER_OAUTH_TOKEN_SECRET="..." \
   LASTFM_API_KEY="..." TMDB_API_KEY="..." \
   python3 build.py
   ```

---

## Task 1: Books data layer

**Files:**
- Modify: `build.py` — `fetch_goodreads()` and `build_book_html()`

The Goodreads RSS feed includes `<book_image_url>`, `<book_description>`, and `<link>` fields we're not currently reading.

### Step 1: Update `fetch_goodreads()` to extract cover, description, and URL

Find the `fetch_goodreads` function (around line 108). Replace the loop body to also extract the new fields:

```python
def fetch_goodreads(rss_url: str, limit: int = 0) -> list[dict]:
    """Return a list of {title, author, rating, cover, description, url} dicts from the RSS feed."""
    req = urllib.request.Request(rss_url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=15) as resp:
        tree = ET.parse(resp)

    books = []
    for item in tree.findall(".//item"):
        title_el = item.find("title")
        author_el = item.find("author_name")
        rating_el = item.find("user_rating")
        cover_el = item.find("book_image_url")
        desc_el = item.find("book_description")
        link_el = item.find("link")

        if title_el is None or title_el.text is None:
            continue

        title = title_el.text.strip()
        author = author_el.text.strip() if author_el is not None and author_el.text else "Unknown"
        rating_text = rating_el.text.strip() if rating_el is not None and rating_el.text else "0"
        rating = min(int(rating_text), 5) if rating_text.isdigit() else 0
        cover = cover_el.text.strip() if cover_el is not None and cover_el.text else ""
        description = desc_el.text.strip() if desc_el is not None and desc_el.text else ""
        if len(description) > 400:
            description = description[:397] + "…"
        url = link_el.text.strip() if link_el is not None and link_el.text else ""

        books.append({
            "title": title, "author": author, "rating": rating,
            "cover": cover, "description": description, "url": url,
        })

        if limit and len(books) >= limit:
            break

    return books
```

### Step 2: Update `build_book_html()` to emit data-* attrs

Find `build_book_html` (around line 135). Replace it entirely:

```python
def build_book_html(books: list[dict]) -> str:
    """Turn a list of books into panel-row divs."""
    if not books:
        return '                <div class="panel-row"><div class="row-content">Nothing at the moment — check back soon.</div></div>'
    lines = []
    for i, book in enumerate(books):
        t = html.escape(book["title"])
        a = html.escape(book["author"])
        rating = book.get("rating", 0)
        idx = f"{i + 1:02d}"

        # Data attrs for modal
        dt = html.escape(book["title"], quote=True)
        da = html.escape(book["author"], quote=True)
        data = (
            f' role="button" tabindex="0"'
            f' data-modal-type="book"'
            f' data-title="{dt}"'
            f' data-author="{da}"'
        )
        if rating:
            data += f' data-stars="{"★" * rating}"'
        if book.get("cover"):
            data += f' data-cover="{html.escape(book["cover"], quote=True)}"'
        if book.get("description"):
            data += f' data-description="{html.escape(book["description"], quote=True)}"'
        if book.get("url"):
            data += f' data-url="{html.escape(book["url"], quote=True)}"'

        if rating:
            aria = f' aria-label="Rated {rating} out of 5"'
            stars_html = f'\n                  <span class="row-meta book-stars"{aria}>{"★" * rating}</span>'
        else:
            stars_html = ""
        lines.append(
            f'                <div class="panel-row"{data}>\n'
            f'                  <span class="row-index">{idx}</span>\n'
            f'                  <div class="row-content">\n'
            f'                    <div class="book-title">{t}</div>\n'
            f'                    <div class="book-author">{a}</div>\n'
            f'                  </div>{stars_html}\n'
            f'                </div>'
        )
    return "\n".join(lines)
```

### Step 3: Verify

Run build and confirm the books panel rows have data attrs:

```bash
python3 build.py 2>&1 | grep -i goodreads
grep -o 'data-modal-type="book"' index.html | wc -l
# Expected: 5 (or however many books are on the read shelf)
grep -o 'data-cover=' index.html | wc -l
# Expected: same count (if Goodreads provides covers)
```

### Step 4: Commit

```bash
git add build.py
git commit -m "feat: add data-* attrs to book panel rows for modal"
```

---

## Task 2: TMDB integration + Films data layer

**Files:**
- Modify: `build.py` — add constants, `fetch_tmdb_data()`, `enrich_films_with_tmdb()`, `build_film_html()`

### Step 1: Add TMDB constants after the Last.fm constant (around line 92)

Add after `LASTFM_LIMIT = CONFIG["sources"]["lastfm"]["limit"]`:

```python
TMDB_API_KEY = os.environ.get("TMDB_API_KEY", "")
TMDB_API = "https://api.themoviedb.org/3"
TMDB_IMG = "https://image.tmdb.org/t/p/w300"
```

### Step 2: Add `fetch_tmdb_data()` and `enrich_films_with_tmdb()` helpers

Add these two functions directly before `build_film_html()` (around line 235):

```python
def fetch_tmdb_data(title: str, year: str, api_key: str) -> dict:
    """Fetch poster, director, and synopsis from TMDB. Returns {} on failure."""
    if not api_key:
        return {}
    params = urllib.parse.urlencode({"query": title, "year": year, "api_key": api_key})
    req = urllib.request.Request(
        f"{TMDB_API}/search/movie?{params}",
        headers={"User-Agent": "Mozilla/5.0"},
    )
    with urllib.request.urlopen(req, timeout=10) as resp:
        data = json.loads(resp.read().decode())
    results = data.get("results", [])
    if not results:
        return {}
    movie = results[0]
    movie_id = movie.get("id")
    poster_path = movie.get("poster_path", "")
    overview = movie.get("overview", "")
    if len(overview) > 400:
        overview = overview[:397] + "…"

    director = ""
    if movie_id:
        req2 = urllib.request.Request(
            f"{TMDB_API}/movie/{movie_id}/credits?api_key={api_key}",
            headers={"User-Agent": "Mozilla/5.0"},
        )
        with urllib.request.urlopen(req2, timeout=10) as resp2:
            credits = json.loads(resp2.read().decode())
        for crew_member in credits.get("crew", []):
            if crew_member.get("job") == "Director":
                director = crew_member.get("name", "")
                break

    return {
        "poster": f"{TMDB_IMG}{poster_path}" if poster_path else "",
        "director": director,
        "synopsis": overview,
    }


def enrich_films_with_tmdb(films: list[dict], api_key: str) -> list[dict]:
    """Add poster/director/synopsis to each film dict via TMDB. Failures are skipped."""
    if not api_key:
        print("  ⚠  TMDB_API_KEY not set — film modals will show Letterboxd data only.")
        return films
    for film in films:
        try:
            tmdb = fetch_tmdb_data(film["title"], film.get("year", ""), api_key)
            film.update(tmdb)
            if tmdb.get("director"):
                print(f"    TMDB: {film['title']} → dir. {tmdb['director']}")
        except Exception as e:
            print(f"  ⚠  TMDB lookup failed for {film['title']!r}: {e}")
    return films
```

### Step 3: Update `build_film_html()` to emit data-* attrs

Find `build_film_html` (around line 235) and replace it:

```python
def build_film_html(films: list[dict]) -> str:
    """Turn a list of films into panel-row divs."""
    if not films:
        return '                <div class="panel-row"><div class="row-content">Nothing at the moment — check back soon.</div></div>'
    lines = []
    for i, film in enumerate(films):
        t = html.escape(film["title"])
        y = html.escape(film["year"]) if film.get("year") else ""
        stars = _star_rating(film["rating"])
        idx = f"{i + 1:02d}"

        # Data attrs for modal
        dt = html.escape(film["title"], quote=True)
        data = (
            f' role="button" tabindex="0"'
            f' data-modal-type="film"'
            f' data-title="{dt}"'
        )
        if film.get("year"):
            data += f' data-year="{html.escape(film["year"], quote=True)}"'
        if stars:
            data += f' data-stars="{html.escape(stars, quote=True)}"'
        if film.get("url"):
            data += f' data-url="{html.escape(film["url"], quote=True)}"'
        if film.get("poster"):
            data += f' data-poster="{html.escape(film["poster"], quote=True)}"'
        if film.get("director"):
            data += f' data-director="{html.escape(film["director"], quote=True)}"'
        if film.get("synopsis"):
            data += f' data-synopsis="{html.escape(film["synopsis"], quote=True)}"'

        if stars:
            aria = f' aria-label="Rated {film["rating"]} out of 5"'
            stars_html = f'\n                  <span class="row-meta film-stars"{aria}>{stars}</span>'
        else:
            stars_html = ""
        lines.append(
            f'                <div class="panel-row"{data}>\n'
            f'                  <span class="row-index">{idx}</span>\n'
            f'                  <div class="row-content">\n'
            f'                    <div class="film-title">{t}</div>\n'
            f'                    <div class="film-year">{y}</div>\n'
            f'                  </div>{stars_html}\n'
            f'                </div>'
        )
    return "\n".join(lines)
```

### Step 4: Verify

```bash
TMDB_API_KEY="your_key_here" python3 build.py 2>&1 | grep -i tmdb
grep -o 'data-modal-type="film"' index.html | wc -l
# Expected: 5
grep -o 'data-poster=' index.html | wc -l
# Expected: up to 5 (fewer if some films not found on TMDB)
```

### Step 5: Commit

```bash
git add build.py
git commit -m "feat: add TMDB integration and data-* attrs to film panel rows"
```

---

## Task 3: Last.fm enrichment + Music data layer

**Files:**
- Modify: `build.py` — `fetch_lastfm_top_tracks()`, new helpers, `build_music_html()`

### Step 1: Add `_strip_html()` helper near the top of the file

Add this helper near the other small helpers (e.g. just before `_star_rating`):

```python
def _strip_html(text: str) -> str:
    """Strip HTML tags and decode entities from a string."""
    text = re.sub(r"<[^>]+>", "", text)
    return html.unescape(text).strip()
```

### Step 2: Update `fetch_lastfm_top_tracks()` to extract track URL

Find the `tracks.append({` call inside `fetch_lastfm_top_tracks` (around line 650). Add the `"url"` field:

```python
        tracks.append({
            "title": track.get("name", ""),
            "artist": track.get("artist", {}).get("name", ""),
            "plays": int(track.get("playcount", 0) or 0),
            "url": track.get("url", ""),
        })
```

### Step 3: Add `fetch_lastfm_track_info()`, `fetch_lastfm_artist_info()`, and `enrich_tracks_with_lastfm()` helpers

Add these three functions directly before `build_music_html()`:

```python
def fetch_lastfm_track_info(title: str, artist: str, api_key: str) -> dict:
    """Return {album} dict from Last.fm track.getInfo."""
    params = urllib.parse.urlencode({
        "method": "track.getInfo",
        "track": title,
        "artist": artist,
        "api_key": api_key,
        "format": "json",
    })
    req = urllib.request.Request(f"{LASTFM_API}?{params}", headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=10) as resp:
        data = json.loads(resp.read().decode())
    album = data.get("track", {}).get("album", {}).get("title", "")
    return {"album": album}


def fetch_lastfm_artist_info(artist: str, api_key: str) -> dict:
    """Return {bio} dict from Last.fm artist.getInfo."""
    params = urllib.parse.urlencode({
        "method": "artist.getInfo",
        "artist": artist,
        "api_key": api_key,
        "format": "json",
    })
    req = urllib.request.Request(f"{LASTFM_API}?{params}", headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=10) as resp:
        data = json.loads(resp.read().decode())
    bio_raw = data.get("artist", {}).get("bio", {}).get("summary", "")
    bio = _strip_html(bio_raw)
    # Last.fm appends a "Read more on Last.fm" link — strip it
    bio = re.sub(r"\s*Read more about\b.*$", "", bio, flags=re.IGNORECASE | re.DOTALL).strip()
    if len(bio) > 300:
        bio = bio[:297] + "…"
    return {"bio": bio}


def enrich_tracks_with_lastfm(tracks: list[dict], api_key: str) -> list[dict]:
    """Add album and artist bio to each track dict. Failures are skipped."""
    if not api_key:
        return tracks
    artist_bios: dict[str, str] = {}
    for track in tracks:
        artist = track["artist"]
        try:
            info = fetch_lastfm_track_info(track["title"], artist, api_key)
            track.update(info)
        except Exception as e:
            print(f"  ⚠  Last.fm track.getInfo failed for {track['title']!r}: {e}")
        if artist not in artist_bios:
            try:
                a_info = fetch_lastfm_artist_info(artist, api_key)
                artist_bios[artist] = a_info.get("bio", "")
            except Exception as e:
                print(f"  ⚠  Last.fm artist.getInfo failed for {artist!r}: {e}")
                artist_bios[artist] = ""
        track["bio"] = artist_bios.get(artist, "")
    return tracks
```

### Step 4: Update `build_music_html()` to emit data-* attrs

Find `build_music_html` (around line 657) and replace it:

```python
def build_music_html(tracks: list[dict]) -> str:
    """Turn a list of tracks into panel-row divs."""
    if not tracks:
        return '                <div class="panel-row"><div class="row-content">Nothing at the moment — check back soon.</div></div>'
    lines = []
    for i, track in enumerate(tracks):
        t = html.escape(track["title"])
        a = html.escape(track["artist"])
        p = track["plays"]
        play_word = "play" if p == 1 else "plays"
        idx = f"{i + 1:02d}"

        # Data attrs for modal
        dt = html.escape(track["title"], quote=True)
        da = html.escape(track["artist"], quote=True)
        data = (
            f' role="button" tabindex="0"'
            f' data-modal-type="music"'
            f' data-title="{dt}"'
            f' data-artist="{da}"'
            f' data-plays="{p}"'
        )
        if track.get("url"):
            data += f' data-url="{html.escape(track["url"], quote=True)}"'
        if track.get("album"):
            data += f' data-album="{html.escape(track["album"], quote=True)}"'
        if track.get("bio"):
            data += f' data-bio="{html.escape(track["bio"], quote=True)}"'

        lines.append(
            f'                <div class="panel-row"{data}>\n'
            f'                  <span class="row-index">{idx}</span>\n'
            f'                  <div class="row-content">\n'
            f'                    <div class="track-title">{t}</div>\n'
            f'                    <div class="track-artist">{a}</div>\n'
            f'                  </div>\n'
            f'                  <span class="row-meta"><span class="play-count">{p} {play_word}</span></span>\n'
            f'                </div>'
        )
    return "\n".join(lines)
```

### Step 5: Verify

```bash
LASTFM_API_KEY="your_key" python3 build.py 2>&1 | grep -i "last.fm\|album\|artist"
grep -o 'data-modal-type="music"' index.html | wc -l
# Expected: 5
grep -o 'data-album=' index.html | wc -l
# Expected: up to 5
```

### Step 6: Commit

```bash
git add build.py
git commit -m "feat: add Last.fm track/artist enrichment and data-* attrs to music rows"
```

---

## Task 4: Articles data layer

**Files:**
- Modify: `build.py` — `fetch_instapaper_starred()` and `build_article_html()`

Articles currently wrap their content in an `<a>` tag. We remove that — the row itself becomes the trigger, and the link goes in the modal.

### Step 1: Update `fetch_instapaper_starred()` to extract `description`

Find `fetch_instapaper_starred` (around line 566). Update the `articles.append({` call to include `description`:

```python
        articles.append({
            "title": item.get("title", "Untitled"),
            "url": _strip_tracking_params(item.get("url", "#")),
            "description": item.get("description", ""),
        })
```

### Step 2: Replace `build_article_html()` — remove `<a>` wrapper, add data attrs

Find `build_article_html` (around line 595) and replace it entirely:

```python
def build_article_html(articles: list[dict]) -> str:
    """Turn a list of articles into panel-row divs (modal-triggered, no direct links)."""
    if not articles:
        return '                <div class="panel-row"><div class="row-content">Nothing yet — check back soon.</div></div>'
    lines = []
    for i, article in enumerate(articles):
        t = html.escape(article["title"])
        u = html.escape(article["url"], quote=True)
        domain = urllib.parse.urlparse(article["url"]).hostname or ""
        domain = domain.removeprefix("www.")
        source_html = f'\n                    <span class="article-source">{html.escape(domain)}</span>' if domain else ""
        idx = f"{i + 1:02d}"

        # Data attrs for modal
        dt = html.escape(article["title"], quote=True)
        data = (
            f' role="button" tabindex="0"'
            f' data-modal-type="article"'
            f' data-title="{dt}"'
            f' data-url="{u}"'
        )
        if domain:
            data += f' data-source="{html.escape(domain, quote=True)}"'
        desc = article.get("description", "")
        if len(desc) > 400:
            desc = desc[:397] + "…"
        if desc:
            data += f' data-description="{html.escape(desc, quote=True)}"'

        lines.append(
            f'                <div class="panel-row"{data}>\n'
            f'                  <span class="row-index">{idx}</span>\n'
            f'                  <div class="row-content">\n'
            f'                    <div class="article-title">{t}</div>{source_html}\n'
            f'                  </div>\n'
            f'                </div>'
        )
    return "\n".join(lines)
```

### Step 3: Verify

```bash
# Run build with Instapaper credentials
INSTAPAPER_CONSUMER_KEY="..." INSTAPAPER_CONSUMER_SECRET="..." \
INSTAPAPER_OAUTH_TOKEN="..." INSTAPAPER_OAUTH_TOKEN_SECRET="..." \
python3 build.py 2>&1 | grep -i instapaper

grep -o 'data-modal-type="article"' index.html | wc -l
# Expected: 5

# Confirm no <a> tags inside article rows
grep -A5 'data-modal-type="article"' index.html | grep '<a '
# Expected: no output (no <a> inside article rows)
```

### Step 4: Commit

```bash
git add build.py
git commit -m "feat: add data-* attrs to article rows; remove inner link (moves to modal)"
```

---

## Task 5: Wire up `main()` and GitHub Actions

**Files:**
- Modify: `build.py` — `cmd_build()` function
- Modify: `.github/workflows/build.yml`

### Step 1: Update `cmd_build()` to call the two enrichment functions

In `cmd_build()`, find the Letterboxd section:
```python
            films = fetch_letterboxd(LETTERBOXD_RSS, LETTERBOXD_LIMIT)
            print(f"  Found {len(films)} recent film(s).")
            src = inject(src, LETTERBOXD_PATTERN, build_film_html(films), "letterboxd")
```

Add the enrichment call between fetch and build:
```python
            films = fetch_letterboxd(LETTERBOXD_RSS, LETTERBOXD_LIMIT)
            print(f"  Found {len(films)} recent film(s).")
            print("Enriching films via TMDB…")
            films = enrich_films_with_tmdb(films, TMDB_API_KEY)
            src = inject(src, LETTERBOXD_PATTERN, build_film_html(films), "letterboxd")
```

Find the Last.fm section:
```python
            tracks = fetch_lastfm_top_tracks(LASTFM_USERNAME, LASTFM_API_KEY, LASTFM_LIMIT)
            print(f"  Found {len(tracks)} top track(s).")
            src = inject(src, MUSIC_PATTERN, build_music_html(tracks), "music")
```

Add enrichment:
```python
            tracks = fetch_lastfm_top_tracks(LASTFM_USERNAME, LASTFM_API_KEY, LASTFM_LIMIT)
            print(f"  Found {len(tracks)} top track(s).")
            print("Enriching tracks via Last.fm…")
            tracks = enrich_tracks_with_lastfm(tracks, LASTFM_API_KEY)
            src = inject(src, MUSIC_PATTERN, build_music_html(tracks), "music")
```

### Step 2: Update docstring at top of `build.py`

Update the module docstring to mention TMDB:
- Change line `"Build script for nicsheehan.com"` section to add: `  7. TMDB (via REST API — TMDB_API_KEY env var, for film poster/director data)`
- Add a Setup section for TMDB after the Last.fm setup section:

```
Setup — TMDB:
    Create a free account at themoviedb.org and generate an API key (v3 auth).
    Set TMDB_API_KEY env var. Used to fetch film posters, directors, and synopses.
    Falls back gracefully if unset — film modals show Letterboxd data only.
```

### Step 3: Add `TMDB_API_KEY` to GitHub Actions workflow

In `.github/workflows/build.yml`, find the `env:` block under "Run build script" and add:
```yaml
          TMDB_API_KEY: ${{ secrets.TMDB_API_KEY }}
```

The full env block should look like:
```yaml
        env:
          GRAVATAR_API_KEY: ${{ secrets.GRAVATAR_API_KEY }}
          LASTFM_API_KEY: ${{ secrets.LASTFM_API_KEY }}
          TMDB_API_KEY: ${{ secrets.TMDB_API_KEY }}
          INSTAPAPER_CONSUMER_KEY: ${{ secrets.INSTAPAPER_CONSUMER_KEY }}
          INSTAPAPER_CONSUMER_SECRET: ${{ secrets.INSTAPAPER_CONSUMER_SECRET }}
          INSTAPAPER_OAUTH_TOKEN: ${{ secrets.INSTAPAPER_OAUTH_TOKEN }}
          INSTAPAPER_OAUTH_TOKEN_SECRET: ${{ secrets.INSTAPAPER_OAUTH_TOKEN_SECRET }}
```

### Step 4: Commit

```bash
git add build.py .github/workflows/build.yml
git commit -m "feat: wire up TMDB and Last.fm enrichment in cmd_build; add TMDB_API_KEY to CI"
```

---

## Task 6: Modal CSS + article CSS cleanup

**Files:**
- Modify: `style.css`

### Step 1: Remove outdated article CSS rules

Find and remove these four rule blocks (around lines 754–791):

```css
.panel-row a {
  text-decoration: none;
  color: inherit;
  display: block;
}

.panel-row a:hover .article-title {
  color: var(--accent-hover);
  text-decoration-color: var(--accent-hover);
}

.panel-row a:focus-visible {
  outline: none;
}

.panel-row a:focus-visible .article-title {
  outline: 1px solid var(--accent);
  outline-offset: 2px;
}
```

Also remove the `.article-row-inner` rules in the desktop media query (around lines 881–892). Look for:
```css
  .article-row-inner {
    ...
  }

  .article-row-inner > div {
    ...
  }
```
Remove both blocks.

Also update `.article-title` — remove the `text-decoration` lines since the title is no longer inside a link:
```css
.article-title {
  font-family: var(--font-mono);
  font-size: 0.75rem;
  font-weight: 400;
  color: var(--text-primary);
  line-height: 1.45;
  text-shadow: 0 0 6px rgba(180, 210, 255, 0.12);
}
```
(Remove `text-decoration: underline`, `text-decoration-color`, `text-underline-offset`, and `transition`.)

Generalise the articles-only hover rule (around line 567). Change:
```css
.panel--articles .panel-row:hover {
  background: var(--panel-hover);
}
```
To (covers all interactive rows):
```css
.panel-row[role="button"]:hover {
  background: var(--panel-hover);
}
```

### Step 2: Add row interactivity styles

After `.panel-row:last-child { border-bottom: none; }` (around line 585), add:

```css
/* Interactive rows (modal trigger) */
.panel-row[role="button"] {
  cursor: pointer;
}

.panel-row[role="button"]:focus-visible {
  outline: 1px solid var(--accent);
  outline-offset: -2px;
}
```

### Step 3: Add modal CSS

Add the following block at the end of `style.css`, before the closing media query or at the very end of the file:

```css
/* ──────────────────────────────────────────────
   ITEM DETAIL MODAL
   ────────────────────────────────────────────── */

.modal-overlay {
  position: fixed;
  inset: 0;
  z-index: 200;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: var(--space-4);
  background: rgba(5, 10, 20, 0.85);
}

@supports (backdrop-filter: blur(1px)) {
  .modal-overlay { backdrop-filter: blur(2px); }
}

@media (prefers-reduced-motion: no-preference) {
  .modal-overlay { animation: modal-fade-in 0.15s ease; }
}

@keyframes modal-fade-in {
  from { opacity: 0; }
  to   { opacity: 1; }
}

.modal-box {
  background: var(--panel);
  border-top: 4px solid var(--modal-accent, var(--accent));
  max-width: 400px;
  width: 100%;
  max-height: calc(100vh - 4rem);
  overflow-y: auto;
  font-family: var(--font-mono);
}

/* Accent colour per content type */
.modal-box[data-modal-type="book"]    { --modal-accent: #22c55e; }
.modal-box[data-modal-type="film"]    { --modal-accent: #f59e0b; }
.modal-box[data-modal-type="music"]   { --modal-accent: #a855f7; }
.modal-box[data-modal-type="article"] { --modal-accent: #3b82f6; }

/* Header band — matches .panel-header rhythm */
.modal-header {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  padding: var(--space-3) var(--space-5);
  border-bottom: 1px solid var(--border);
}

.modal-close {
  background: none;
  border: none;
  cursor: pointer;
  color: var(--text-tertiary);
  font-family: var(--font-mono);
  font-size: 0.75rem;
  padding: 0;
  line-height: 1;
  flex-shrink: 0;
}

.modal-close:hover { color: var(--text-primary); }

.modal-close:focus-visible {
  outline: 1px solid var(--accent);
  outline-offset: 2px;
}

.modal-type-label {
  color: var(--modal-accent, var(--accent));
  font-size: 0.65rem;
  letter-spacing: 0.08em;
  flex: 1;
}

.modal-index {
  color: var(--text-tertiary);
  font-size: 0.65rem;
  letter-spacing: 0.04em;
  flex-shrink: 0;
}

/* Content area */
.modal-content {
  display: flex;
  gap: var(--space-4);
  padding: var(--space-5);
}

.modal-cover {
  width: 80px;
  height: auto;
  max-height: 120px;
  object-fit: cover;
  flex-shrink: 0;
  align-self: flex-start;
}

.modal-cover[data-music] {
  width: 64px;
}

.modal-body {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
}

/* Typography */
.modal-title {
  font-size: 0.85rem;
  font-weight: 700;
  color: var(--text-primary);
  line-height: 1.3;
  text-shadow: 0 0 6px rgba(180, 210, 255, 0.12);
  margin: 0;
}

.modal-meta {
  font-size: 0.7rem;
  color: var(--text-secondary);
  margin: 0;
  line-height: 1.4;
}

.modal-desc {
  font-size: 0.7rem;
  color: var(--text-tertiary);
  margin: 0;
  line-height: 1.5;
  display: -webkit-box;
  -webkit-line-clamp: 4;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

/* Outbound link — matches .panel-footer-link style */
.modal-link {
  display: inline-block;
  color: var(--text-tertiary);
  font-family: var(--font-mono);
  font-size: 0.6rem;
  letter-spacing: 0.06em;
  text-decoration: none;
  margin-top: var(--space-1);
}

.modal-link:hover { color: var(--text-secondary); }

.modal-link:focus-visible {
  outline: 1px solid var(--accent);
  outline-offset: 2px;
}
```

### Step 4: Verify

Open `index.html` in browser — no console errors, articles still look correct visually (just without underlines). Hover over any panel row — should show `cursor: pointer`.

### Step 5: Commit

```bash
git add style.css
git commit -m "feat: add modal CSS; remove old article link CSS; generalise row hover"
```

---

## Task 7: Modal HTML

**Files:**
- Modify: `index.html`

The modal element must be placed **outside all `<!-- marker:start/end -->` blocks** so it survives build regeneration. Place it just before `</body>`.

### Step 1: Find the closing `</body>` tag in index.html

Look for the existing inline `<script>` block near the end of `<body>`. The modal HTML goes immediately after the existing scripts, before `</body>`.

### Step 2: Add the modal element

Insert this block just before `</body>`:

```html
      <!-- Item detail modal -->
      <div id="detail-modal" class="modal-overlay" role="dialog"
           aria-modal="true" aria-labelledby="modal-title" hidden>
        <div class="modal-box">
          <div class="modal-header">
            <button class="modal-close" aria-label="Close">[ X ]</button>
            <span class="modal-type-label" aria-hidden="true"></span>
            <span class="modal-index" aria-hidden="true"></span>
          </div>
          <div class="modal-content">
            <img class="modal-cover" src="" alt="" hidden>
            <div class="modal-body">
              <h2 class="modal-title" id="modal-title"></h2>
              <p class="modal-meta"></p>
              <p class="modal-desc" hidden></p>
              <a class="modal-link" target="_blank" rel="noopener noreferrer"></a>
            </div>
          </div>
        </div>
      </div>
```

### Step 3: Verify

Open `index.html` in a browser. The modal should not be visible (it has `hidden`). Check the DOM inspector — `#detail-modal` should exist. No visual change to the page.

### Step 4: Commit

```bash
git add index.html
git commit -m "feat: add static modal HTML element to index.html"
```

---

## Task 8: Modal JS

**Files:**
- Modify: `index.html`

Add a new inline `<script>` block immediately after the modal HTML (before `</body>`).

### Step 1: Add the modal script block

```html
      <script>
        (function () {
          var overlay = document.getElementById('detail-modal');
          var box = overlay.querySelector('.modal-box');
          var closeBtn = overlay.querySelector('.modal-close');
          var coverEl = overlay.querySelector('.modal-cover');
          var titleEl = overlay.querySelector('.modal-title');
          var metaEl = overlay.querySelector('.modal-meta');
          var descEl = overlay.querySelector('.modal-desc');
          var linkEl = overlay.querySelector('.modal-link');
          var typeLabelEl = overlay.querySelector('.modal-type-label');
          var indexEl = overlay.querySelector('.modal-index');
          var activeRow = null;

          var TYPE_LABELS = {
            book:    '[▓] BOOKS',
            film:    '[▶] FILMS',
            music:   '[♫] MUSIC',
            article: '[≡] ARTICLES',
          };

          function openModal(row) {
            var type = row.dataset.modalType;
            var title = row.dataset.title || '';
            var url = row.dataset.url || '#';

            // Accent colour and type label
            box.dataset.modalType = type;
            typeLabelEl.textContent = TYPE_LABELS[type] || '';

            // Item index within its panel (e.g. "02 / 05")
            var panelBody = row.closest('.panel-body');
            var siblings = panelBody
              ? Array.from(panelBody.querySelectorAll('.panel-row[role="button"]'))
              : [row];
            var idx = siblings.indexOf(row) + 1;
            indexEl.textContent = idx + ' / ' + siblings.length;

            // Title
            titleEl.textContent = title;

            // Cover / poster image
            var coverSrc = type === 'film'
              ? (row.dataset.poster || '')
              : (row.dataset.cover || '');
            if (coverSrc) {
              coverEl.src = coverSrc;
              coverEl.alt = title;
              if (type === 'music') {
                coverEl.setAttribute('data-music', '');
              } else {
                coverEl.removeAttribute('data-music');
              }
              coverEl.hidden = false;
            } else {
              coverEl.src = '';
              coverEl.hidden = true;
            }

            // Meta, description, link — per content type
            var meta = '', desc = '', linkText = '';

            if (type === 'book') {
              var parts = [row.dataset.author, row.dataset.stars].filter(Boolean);
              meta = parts.join(' · ');
              desc = row.dataset.description || '';
              linkText = '→ View on Goodreads';
            } else if (type === 'film') {
              var director = row.dataset.director ? 'dir. ' + row.dataset.director : '';
              var parts = [row.dataset.year, row.dataset.stars, director].filter(Boolean);
              meta = parts.join(' · ');
              desc = row.dataset.synopsis || '';
              linkText = '→ View on Letterboxd';
            } else if (type === 'music') {
              var plays = row.dataset.plays ? row.dataset.plays + ' plays' : '';
              var parts = [row.dataset.artist, row.dataset.album, plays].filter(Boolean);
              meta = parts.join(' · ');
              desc = row.dataset.bio || '';
              linkText = '→ Listen on Last.fm';
            } else if (type === 'article') {
              meta = row.dataset.source || '';
              desc = row.dataset.description || '';
              linkText = meta ? '→ Read on ' + meta : '→ Read article';
            }

            metaEl.textContent = meta;

            if (desc) {
              descEl.textContent = desc;
              descEl.hidden = false;
            } else {
              descEl.hidden = true;
            }

            linkEl.textContent = linkText;
            linkEl.href = url;

            // Show modal
            overlay.hidden = false;
            document.body.style.overflow = 'hidden';
            activeRow = row;
            closeBtn.focus();
          }

          function closeModal() {
            overlay.hidden = true;
            document.body.style.overflow = '';
            if (activeRow) {
              activeRow.focus();
              activeRow = null;
            }
          }

          // Attach click and keyboard to each interactive row
          document.querySelectorAll('.panel-row[role="button"]').forEach(function (row) {
            row.addEventListener('click', function () { openModal(row); });
            row.addEventListener('keydown', function (e) {
              if (e.key === 'Enter' || e.key === ' ') {
                e.preventDefault();
                openModal(row);
              }
            });
          });

          // Close handlers
          closeBtn.addEventListener('click', closeModal);
          overlay.addEventListener('click', function (e) {
            if (e.target === overlay) closeModal();
          });
          document.addEventListener('keydown', function (e) {
            if (!overlay.hidden && e.key === 'Escape') closeModal();
          });

          // Basic tab trap within modal
          overlay.addEventListener('keydown', function (e) {
            if (overlay.hidden || e.key !== 'Tab') return;
            var focusable = Array.from(
              overlay.querySelectorAll('button, a[href]')
            ).filter(function (el) { return !el.hidden; });
            if (focusable.length === 0) return;
            var first = focusable[0];
            var last = focusable[focusable.length - 1];
            if (e.shiftKey && document.activeElement === first) {
              e.preventDefault();
              last.focus();
            } else if (!e.shiftKey && document.activeElement === last) {
              e.preventDefault();
              first.focus();
            }
          });
        })();
      </script>
```

### Step 2: Verify in browser

Open `index.html` in a browser (after running build.py). Check:
- Click any book row → modal opens with green top border, title, author, stars, cover image (if available), description, "→ View on Goodreads" link
- Click any film row → modal opens with amber border, title, year, director, synopsis, poster (if TMDB found it)
- Click any music row → modal opens with purple border, title, artist, album, play count, bio
- Click any article row → modal opens with blue border, title, source domain, description (if Instapaper returned one), link
- Press ESC → modal closes, focus returns to the row
- Click backdrop → modal closes
- Click `[ X ]` → modal closes
- Tab while modal is open → cycles between `[ X ]` and the link
- `→ View on Goodreads` link opens in new tab ✓

### Step 3: Commit

```bash
git add index.html
git commit -m "feat: add modal JS — click panel rows to open item detail modal"
```

---

## Task 9: End-to-end verification and push

### Step 1: Run the full build with all API keys

```bash
git restore og-image.png sitemap.xml   # discard CI artifacts
git pull --rebase origin main          # get latest bot commits

GRAVATAR_API_KEY="..." \
INSTAPAPER_CONSUMER_KEY="..." INSTAPAPER_CONSUMER_SECRET="..." \
INSTAPAPER_OAUTH_TOKEN="..." INSTAPAPER_OAUTH_TOKEN_SECRET="..." \
LASTFM_API_KEY="..." \
TMDB_API_KEY="..." \
python3 build.py
```

### Step 2: Check HTML output

```bash
# All four modal types present
grep -o 'data-modal-type="[a-z]*"' index.html | sort | uniq -c
# Expected: 5 of each type (book, film, music, article) plus ~1-2 books from currently-reading

# No <a> tags inside article rows
python3 -c "
import re
content = open('index.html').read()
# Find article panel-row divs and check for anchors inside
rows = re.findall(r'data-modal-type=\"article\"[^>]*>.*?</div>\s*</div>', content, re.DOTALL)
for row in rows:
    assert '<a ' not in row, f'Found <a> inside article row: {row[:100]}'
print(f'OK: {len(rows)} article rows, none contain <a> tags')
"

# No double-quotes from curly-quote contamination in attrs
grep -P '[\u201c\u201d]' index.html
# Expected: no output
```

### Step 3: Open in browser and manual test

Open `index.html` in a browser (file:// URL or `python3 -m http.server`). Test:
- [ ] All four panel types open a modal on click
- [ ] Modal header shows correct type label (`[▓] BOOKS` etc.) and item index (`01 / 05`)
- [ ] Book modal: title, author, stars, cover image (if available), description, Goodreads link
- [ ] Film modal: title, year, stars, director, synopsis, poster (if TMDB hit), Letterboxd link
- [ ] Music modal: title, artist, album, play count, bio, Last.fm link
- [ ] Article modal: title, source domain, description (if present), article link
- [ ] ESC closes modal, focus returns to row
- [ ] Clicking backdrop closes modal
- [ ] `[ X ]` button closes modal
- [ ] Tab cycles between `[ X ]` and the link while modal is open
- [ ] Page scroll is locked while modal is open

### Step 4: Update roadmap and docs

In `docs/roadmap.md`, mark iteration 9 complete:

```markdown
## Iteration 9 — Item detail modal + links out ✅ shipped 2026-02-28
```

Check the checkboxes:
```markdown
- [x] Click any panel item → in-page modal overlay (accent border, monospace, ESC to dismiss)
- [x] Modal shows richer data stored as `data-*` attributes at build time: book cover + description, Last.fm album + bio, article excerpt
- [x] "View on [Service] →" link inside each modal
- [x] TMDB integration for films — poster, director, synopsis
```

### Step 5: Update MEMORY.md with iteration 9 facts

Update `/Users/nicholassheehan/.claude/projects/-Users-nicholassheehan-Documents-Claude-Files-Personal-website/memory/MEMORY.md`:
- Add `TMDB_API_KEY` to GitHub Secrets table
- Update "Next up" to point to Iteration 10
- Add iteration 9 notes about modal data attrs and JS behavior to the Architecture section

### Step 6: Push

```bash
git restore og-image.png sitemap.xml
git pull --rebase origin main
git push origin main
```

---

## Notes for implementer

- `re` is already imported in `build.py` — no new imports needed
- `html.escape(value)` escapes `&`, `<`, `>` for display; `html.escape(value, quote=True)` also escapes `"` — always use `quote=True` for HTML attribute values
- The `<!-- goodreads:start/end -->` marker (hidden div) also uses `build_book_html()` — those rows will get `role="button"` too, but they're in `<div hidden aria-hidden="true">` so they won't be visible or AT-accessible
- TMDB is rate-limited (40 requests/10 seconds) — our 10 calls per build are well within limits
- If TMDB returns no result for a film (e.g. "Dead Calm" without year mismatch), the film modal still works — just shows title/year/stars/Letterboxd link without poster or director
- Letterboxd film URLs are review-specific (e.g. `https://letterboxd.com/tonic2/film/dead-calm/`) — already fetched in `fetch_letterboxd()`
