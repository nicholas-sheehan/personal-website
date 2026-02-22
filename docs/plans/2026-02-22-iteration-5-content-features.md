# Iteration 5 — Content Features Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add currently-reading status strip, linked panel headings with source subtitles, and a live footer countdown to the next scheduled build.

**Architecture:** Three independent changes: (1) `build_now_reading_html()` generates prose HTML from the Goodreads currently-reading shelf and injects it into the existing `goodreads-now` markers; (2) `index.html` panel headers get a wrapper div + link + source subtitle, with matching CSS in `style.css`; (3) `build.py` calculates the next 22:00 UTC build time and injects it as a `data-next` attribute, a static inline `<script>` in `index.html` ticks the countdown every minute, and `style.css` adds the pulsing dot animation.

**Note:** "Colophon copy: Powered by → Built daily from" (roadmap item 4) is already done — `index.html` already reads "Built daily from Gravatar, Goodreads, Letterboxd, Instapaper & Last.fm." No action needed.

**Tech Stack:** Python 3.9+ (local) / 3.12 (CI), stdlib only (`datetime`, `timedelta`), CSS animations, ~230-byte vanilla JS

---

### Task 1: Currently reading status strip

**Files:**
- Modify: `index.html` lines 937–940 (goodreads-now markers)
- Modify: `build.py` — add `GOODREADS_NOW_PATTERN`, `build_now_reading_html()`, wire into `cmd_build()`

#### Background

The `<!-- goodreads-now:start/end -->` markers are currently adjacent (just a newline between them). The `_make_pattern()` regex requires at least one content line between markers — adjacent markers silently fail to inject (prints WARNING). Fix: add a placeholder line. Then implement the Python function.

The CSS for `.status-strip`, `.status-strip-label`, `.status-strip-sep`, `.status-strip-text` is already in `style.css` — no CSS changes needed for this task.

---

**Step 1: Add placeholder between goodreads-now markers in `index.html`**

Find lines 937–940:
```html
          <!-- ── NOW READING STATUS STRIP (reserved for Iteration 5) ── -->
<!-- goodreads-now:start -->
<!-- goodreads-now:end -->
          <!-- Currently reading marker (hidden, reintroduced in Iteration 5) -->
```

Replace with:
```html
          <!-- ── NOW READING STATUS STRIP ── -->
<!-- goodreads-now:start -->
            <!-- currently reading: injected at build time -->
<!-- goodreads-now:end -->
          <!-- Currently reading data (hidden — used by status strip above) -->
```

---

**Step 2: Add `GOODREADS_NOW_PATTERN` to `build.py`**

Find (around line 668):
```python
GOODREADS_PATTERN = _make_pattern("goodreads")
GOODREADS_READ_PATTERN = _make_pattern("goodreads-read")
```

Replace with:
```python
GOODREADS_PATTERN = _make_pattern("goodreads")
GOODREADS_NOW_PATTERN = _make_pattern("goodreads-now")
GOODREADS_READ_PATTERN = _make_pattern("goodreads-read")
```

---

**Step 3: Add `build_now_reading_html()` to `build.py`**

Add this function immediately after `build_book_html()` (around line 146):

```python
def build_now_reading_html(books: list[dict]) -> str:
    """Generate status strip HTML for currently-reading shelf.

    0 books  → placeholder comment (section invisible)
    1 book   → "Currently reading <em>Title</em> by Author"
    2+ books → "Currently reading <em>Title 1</em>, <em>Title 2</em>"
    """
    if not books:
        return "            <!-- no books currently reading -->"
    if len(books) == 1:
        t = html.escape(books[0]["title"])
        a = html.escape(books[0]["author"])
        text = f"Currently reading <em>{t}</em> by {a}"
    else:
        titles = ", ".join(f"<em>{html.escape(b['title'])}</em>" for b in books)
        text = f"Currently reading {titles}"
    return (
        '            <div class="status-strip">\n'
        '              <span class="status-strip-label">Now reading</span>\n'
        '              <span class="status-strip-sep">›</span>\n'
        f'              <span class="status-strip-text">{text}</span>\n'
        '            </div>'
    )
```

---

**Step 4: Wire `build_now_reading_html()` into `cmd_build()`**

Find this block in `cmd_build()` (inside the Goodreads try block, around line 784):
```python
        books = fetch_goodreads(GOODREADS_RSS)
        print(f"  Found {len(books)} book(s) on currently-reading shelf.")
        src = inject(src, GOODREADS_PATTERN, build_book_html(books), "goodreads")
```

Replace with:
```python
        books = fetch_goodreads(GOODREADS_RSS)
        print(f"  Found {len(books)} book(s) on currently-reading shelf.")
        src = inject(src, GOODREADS_PATTERN, build_book_html(books), "goodreads")
        src = inject(src, GOODREADS_NOW_PATTERN, build_now_reading_html(books), "goodreads-now")
```

---

**Step 5: Parse check**

```bash
python3 -c "import ast; ast.parse(open('build.py').read()); print('OK')"
```

Expected: `OK`

---

**Step 6: Logic test**

```bash
python3 -c "
import build

# 0 books: comment placeholder
r0 = build.build_now_reading_html([])
assert 'status-strip' not in r0, 'unexpected strip when no books'
assert '<!--' in r0, 'expected placeholder comment'
print('OK: 0 books:', r0.strip())

# 1 book: prose with author
r1 = build.build_now_reading_html([{'title': 'Zorba the Greek', 'author': 'Nikos Kazantzakis'}])
assert 'status-strip' in r1
assert '<em>Zorba the Greek</em>' in r1
assert 'Nikos Kazantzakis' in r1
print('OK: 1 book contains title and author')

# 2 books: titles only, no authors
r2 = build.build_now_reading_html([
    {'title': 'Book A', 'author': 'Author A'},
    {'title': 'Book B', 'author': 'Author B'},
])
assert '<em>Book A</em>' in r2 and '<em>Book B</em>' in r2
assert 'Author A' not in r2, 'authors should be dropped for 2+ books'
print('OK: 2+ books: titles only')

# XSS: special chars escaped
r_xss = build.build_now_reading_html([{'title': '<script>', 'author': '&amp;'}])
assert '<script>' not in r_xss, 'title not escaped'
print('OK: XSS chars escaped')
"
```

Expected: four `OK` lines.

---

**Step 7: Verify marker has placeholder**

```bash
python3 -c "
src = open('index.html').read()
assert '<!-- goodreads-now:start -->' in src
# Confirm there's content between the markers (not adjacent)
import re
m = re.search(r'<!-- goodreads-now:start -->\n(.*?)\n.*?<!-- goodreads-now:end -->', src, re.DOTALL)
assert m and m.group(1).strip(), 'markers are adjacent — no content between them'
print('OK: placeholder present between goodreads-now markers')
"
```

Expected: `OK`

---

**Step 8: Commit**

```bash
git add index.html build.py
git commit -m "Add currently-reading status strip (build_now_reading_html + goodreads-now marker)"
```

---

### Task 2: Section headings link to sources

**Files:**
- Modify: `index.html` — all four `panel-header` blocks
- Modify: `style.css` — add `.panel-heading`, `.panel-label-link`, `.section-arrow`, `.section-source`

#### Background

Currently each panel header is:
```html
<div class="panel-header">
  <h2 class="panel-label" ...>Books</h2>
  <span class="panel-count">recently read</span>
</div>
```

The new structure wraps the h2 + source subtitle in a `.panel-heading` container:
```html
<div class="panel-header">
  <div class="panel-heading">
    <h2 class="panel-label" ...>
      <a href="..." class="panel-label-link">Books <svg class="section-arrow">...</svg></a>
    </h2>
    <p class="section-source">via Goodreads</p>
  </div>
  <span class="panel-count">recently read</span>
</div>
```

- **Books** → linked to Goodreads, subtitle "via Goodreads"
- **Films** → linked to Letterboxd, subtitle "on Letterboxd as tonic2"
- **Music** → no link, subtitle "via Last.fm"
- **Articles** → no link, subtitle "saved in Instapaper"

The arrow SVG (`section-arrow`) is hidden by default and fades in on hover/focus.

---

**Step 1: Add CSS to `style.css`**

Add this block in `style.css` just before the `/* --- BOOKS rows --- */` comment (after the `.panel-count` rule):

```css
/* Panel heading wrapper — stacks label above source subtitle */
.panel-heading {
  display: flex;
  flex-direction: column;
  gap: 0.15rem;
}

/* Linked panel label — strips link decoration, inherits panel-label styles */
.panel-label-link {
  text-decoration: none;
  color: inherit;
  display: flex;
  align-items: center;
  gap: 0.3em;
}

.panel-label-link:focus-visible {
  outline: 1px solid var(--accent);
  outline-offset: 2px;
}

/* External link arrow — invisible until hover/focus */
.section-arrow {
  opacity: 0;
  transition: opacity 0.15s ease;
  flex-shrink: 0;
}

.panel-label-link:hover .section-arrow,
.panel-label-link:focus-visible .section-arrow {
  opacity: 0.65;
}

/* Source subtitle — mono tertiary byline below panel heading */
.section-source {
  font-family: var(--font-mono);
  font-size: 0.6rem;
  font-weight: 400;
  color: var(--text-tertiary);
  letter-spacing: 0.06em;
}
```

---

**Step 2: Update Books panel header in `index.html`**

Find:
```html
              <div class="panel-header">
                <h2 class="panel-label" id="panel-books-label" data-icon="[▓]">Books</h2>
                <span class="panel-count">recently read</span>
              </div>
```

Replace with:
```html
              <div class="panel-header">
                <div class="panel-heading">
                  <h2 class="panel-label" id="panel-books-label" data-icon="[▓]"><a href="https://www.goodreads.com/user/show/175639385" class="panel-label-link" target="_blank" rel="noopener noreferrer">Books<svg class="section-arrow" width="10" height="10" viewBox="0 0 10 10" fill="none" aria-hidden="true"><path d="M2 8L8 2M8 2H3M8 2V7" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/></svg></a></h2>
                  <p class="section-source">via Goodreads</p>
                </div>
                <span class="panel-count">recently read</span>
              </div>
```

---

**Step 3: Update Films panel header in `index.html`**

Find:
```html
              <div class="panel-header">
                <h2 class="panel-label" id="panel-films-label" data-icon="[▶]">Films</h2>
                <span class="panel-count">recently watched</span>
              </div>
```

Replace with:
```html
              <div class="panel-header">
                <div class="panel-heading">
                  <h2 class="panel-label" id="panel-films-label" data-icon="[▶]"><a href="https://letterboxd.com/tonic2" class="panel-label-link" target="_blank" rel="noopener noreferrer">Films<svg class="section-arrow" width="10" height="10" viewBox="0 0 10 10" fill="none" aria-hidden="true"><path d="M2 8L8 2M8 2H3M8 2V7" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/></svg></a></h2>
                  <p class="section-source">on Letterboxd as tonic2</p>
                </div>
                <span class="panel-count">recently watched</span>
              </div>
```

---

**Step 4: Update Music panel header in `index.html`**

Find:
```html
              <div class="panel-header">
                <h2 class="panel-label" id="panel-music-label" data-icon="[♫]">Music</h2>
                <span class="panel-count">top tracks this month</span>
              </div>
```

Replace with:
```html
              <div class="panel-header">
                <div class="panel-heading">
                  <h2 class="panel-label" id="panel-music-label" data-icon="[♫]">Music</h2>
                  <p class="section-source">via Last.fm</p>
                </div>
                <span class="panel-count">top tracks this month</span>
              </div>
```

---

**Step 5: Update Articles panel header in `index.html`**

Find:
```html
              <div class="panel-header">
                <h2 class="panel-label" id="panel-articles-label" data-icon="[//]">Articles</h2>
                <span class="panel-count">reads I recommend</span>
              </div>
```

Replace with:
```html
              <div class="panel-header">
                <div class="panel-heading">
                  <h2 class="panel-label" id="panel-articles-label" data-icon="[//]">Articles</h2>
                  <p class="section-source">saved in Instapaper</p>
                </div>
                <span class="panel-count">reads I recommend</span>
              </div>
```

---

**Step 6: Verify**

```bash
python3 -c "
src = open('index.html').read()

# All four section-source elements present
assert src.count('section-source') == 4, f'Expected 4 .section-source, got {src.count(\"section-source\")}'

# Books and Films have links
assert 'goodreads.com/user/show/175639385' in src, 'Goodreads link missing'
assert 'letterboxd.com/tonic2' in src and 'panel-label-link' in src, 'Letterboxd link missing'

# All four section-arrow SVGs (only 2 panels have links, but check at least 2)
assert src.count('section-arrow') >= 2, 'Expected at least 2 section-arrow SVGs'

# panel-heading wrappers (4 panels)
assert src.count('panel-heading') == 4, f'Expected 4 .panel-heading, got {src.count(\"panel-heading\")}'

print('OK')
"
```

```bash
python3 -c "
css = open('style.css').read()
assert '.panel-heading' in css
assert '.panel-label-link' in css
assert '.section-arrow' in css
assert '.section-source' in css
print('OK: all CSS rules present')
"
```

Expected: `OK` for both.

---

**Step 7: Commit**

```bash
git add index.html style.css
git commit -m "Add linked panel headings and source subtitles for Books, Films, Music, Articles"
```

---

### Task 3: Footer countdown

**Files:**
- Modify: `build.py` — import `timedelta`, add `_next_build_utc()`, update timestamp injection
- Modify: `style.css` — add `@keyframes pulse-breathe`, `.pulse-dot`, `.next-update`
- Modify: `index.html` — add static countdown `<script>` before `<!-- analytics:start -->`

#### Background

The daily build runs at 22:00 UTC. `build.py` calculates the next occurrence of 22:00 UTC after the current build time and injects it as a `data-next` ISO string. The colophon timestamp gets a pulsing dot prepended and a `<span class="next-update">` appended. A tiny static inline `<script>` in `index.html` reads `data-next` and updates the span text every 60 seconds. Without JS: dot + "Last built …" only (graceful degradation).

---

**Step 1: Add `timedelta` to `build.py` imports**

Find:
```python
from datetime import datetime, timezone
```

Replace with:
```python
from datetime import datetime, timedelta, timezone
```

---

**Step 2: Add `_next_build_utc()` to `build.py`**

Add this function just before the `cmd_auth()` function (around line 708):

```python
def _next_build_utc(now: datetime) -> datetime:
    """Return the next scheduled 22:00 UTC build time strictly after now."""
    today_build = now.replace(hour=22, minute=0, second=0, microsecond=0)
    if now < today_build:
        return today_build
    return today_build + timedelta(days=1)
```

---

**Step 3: Update timestamp injection in `cmd_build()`**

Find (around line 842):
```python
    # ── Last built timestamp ──
    now = datetime.now(timezone.utc)
    updated_str = now.strftime("%-d %b %Y at %H:%M UTC")
    updated_html = f'            <p class="colophon-timestamp">Last built {updated_str}</p>'
    src = inject(src, UPDATED_PATTERN, updated_html, "updated")
    print(f"  Timestamp: {updated_str}")
```

Replace with:
```python
    # ── Last built timestamp + countdown ──
    now = datetime.now(timezone.utc)
    next_build = _next_build_utc(now)
    next_iso = next_build.strftime("%Y-%m-%dT%H:%M:%SZ")
    updated_str = now.strftime("%-d %b %Y at %H:%M UTC")
    updated_html = (
        f'            <p class="colophon-timestamp">'
        f'<span class="pulse-dot" aria-hidden="true"></span>'
        f' Last built {updated_str}'
        f'<span class="next-update" data-next="{next_iso}"></span>'
        f'</p>'
    )
    src = inject(src, UPDATED_PATTERN, updated_html, "updated")
    print(f"  Timestamp: {updated_str} · next build: {next_iso}")
```

---

**Step 4: Parse check + logic test for `build.py`**

```bash
python3 -c "import ast; ast.parse(open('build.py').read()); print('OK')"
```

```bash
python3 -c "
from datetime import datetime, timezone
import build

# Before 22:00 UTC: next build is today at 22:00
before = datetime(2026, 2, 22, 10, 30, 0, tzinfo=timezone.utc)
n1 = build._next_build_utc(before)
assert n1.hour == 22 and n1.day == 22 and n1.month == 2, f'Expected 22:00 UTC today, got {n1}'
print('OK: before 22:00 → today at 22:00')

# After 22:00 UTC: next build is tomorrow
after = datetime(2026, 2, 22, 23, 0, 0, tzinfo=timezone.utc)
n2 = build._next_build_utc(after)
assert n2.hour == 22 and n2.day == 23, f'Expected tomorrow at 22:00, got {n2}'
print('OK: after 22:00 → tomorrow at 22:00')

# Exactly at 22:00: counts as past — next is tomorrow
at = datetime(2026, 2, 22, 22, 0, 0, tzinfo=timezone.utc)
n3 = build._next_build_utc(at)
assert n3.day == 23, f'Expected next day when exactly at 22:00, got {n3}'
print('OK: at exactly 22:00 → tomorrow')

# Month rollover: Feb 28 → Mar 1
feb28 = datetime(2026, 2, 28, 23, 0, 0, tzinfo=timezone.utc)
n4 = build._next_build_utc(feb28)
assert n4.month == 3 and n4.day == 1, f'Expected Mar 1, got {n4}'
print('OK: month rollover works')
"
```

Expected: four `OK` lines.

---

**Step 5: Add CSS to `style.css`**

Add this block in `style.css` just before the `/* ── FOOTER / COLOPHON ── */` comment:

```css
/* ──────────────────────────────────────────────
   PULSE DOT + COUNTDOWN
   ────────────────────────────────────────────── */

@keyframes pulse-breathe {
  0%, 100% { opacity: 0.3; transform: scale(0.85); }
  50%       { opacity: 1;   transform: scale(1.15); }
}

.pulse-dot {
  display: inline-block;
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--accent);
  margin-right: var(--space-1);
  vertical-align: middle;
  animation: pulse-breathe 3s ease-in-out infinite;
}

.next-update {
  font-family: var(--font-mono);
  font-size: 0.65rem;
  color: var(--text-dim);
  letter-spacing: 0.06em;
}
```

---

**Step 6: Add static countdown script to `index.html`**

Find:
```html
<!-- analytics:start -->
```

Insert immediately before it:
```html
<script>(function(){var e=document.querySelector('.next-update');if(!e)return;function t(){var n=new Date(e.dataset.next),d=n-new Date();if(d<=0){e.textContent=' · updating soon';return;}var h=Math.floor(d/3600000),m=Math.floor((d%3600000)/60000);e.textContent=' · next in '+h+'h '+m+'m';}t();setInterval(t,60000);})();</script>
<!-- analytics:start -->
```

---

**Step 7: Verify HTML structure**

```bash
python3 -c "
src = open('index.html').read()

# Pulse dot present in colophon timestamp
assert 'pulse-dot' in src, 'pulse-dot span missing'
assert 'next-update' in src, 'next-update span missing'
assert 'data-next=' in src, 'data-next attribute missing'

# Script present before analytics
script_pos = src.index('<script>(function(){var e=document')
analytics_pos = src.index('<!-- analytics:start -->')
assert script_pos < analytics_pos, 'countdown script must appear before analytics marker'

print('OK: pulse-dot, next-update, data-next, and script all present in correct order')
"
```

```bash
python3 -c "
css = open('style.css').read()
assert 'pulse-breathe' in css
assert '.pulse-dot' in css
assert '.next-update' in css
print('OK: pulse CSS present')
"
```

Expected: both `OK`.

---

**Step 8: Commit**

```bash
git add build.py index.html style.css
git commit -m "Add footer countdown: pulsing dot + live next-build timer"
```

---

### Final: run full local build, review, push

**Step 1: Run a full local build (with real credentials if available, or dry-run)**

```bash
python3 build.py
```

If credentials aren't set locally, most sections will print warnings and preserve existing content — that's fine. Confirm no Python errors.

**Step 2: Open `index.html` in a browser and visually verify:**
- Status strip appears between header and content grid (if currently-reading shelf has books)
- Books and Films panel headings have a hover arrow (check with mouse)
- Music and Films panels show source subtitles
- Colophon has pulsing dot + countdown text
- Source subtitles are present on all four panels

**Step 3: Inline the updated CSS into `index.html`**

The build step above already inlines `style.css`, so this is done.

**Step 4: Update the roadmap**

In `.claude/roadmap.md`, mark all Iteration 5 items as done:
```markdown
## Iteration 5 — Content features ✅ shipped 2026-02-22
- [x] Currently reading callout — build.py logic (build_now_reading_html(), new marker)
- [x] Section headings link to sources (+ mono subtitles)
- [x] Footer countdown: pulsing dot (CSS) + "next in 14h 23m" (minimal inline JS, degrades gracefully)
- [x] Colophon copy: "Powered by" → "Built daily from" _(pre-completed in iteration 4)_
```

**Step 5: Push**

```bash
git restore og-image.png sitemap.xml
git pull --rebase origin main
git push origin main
```
