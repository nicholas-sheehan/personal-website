# Iteration 13 — Status Strip Polish Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Polish the now-reading and now-playing status strips: side-by-side on desktop, remove "by" connector, use colour contrast to distinguish title from author/artist.

**Architecture:** Four file edits — CSS rules in `style.css`, Python template in `build.py`, static HTML wrapper and minified JS in `index.html`. No new dependencies.

**Tech Stack:** CSS flex, Python f-strings, vanilla JS DOM manipulation.

---

## Context

- `style.css` is the CSS source — inlined at build time between `<!-- style:start/end -->` markers. Edit `style.css`; the build inlines it.
- `index.html` has two strips between the `</header>` and the content grid. The now-reading strip is between `<!-- goodreads-now:start/end -->` markers (injected by build). The now-playing strip is static HTML (outside markers).
- The now-playing JS is a minified IIFE at the bottom of `<body>`, outside all markers — edits to it persist across builds.
- Local build: `python3 build.py` (no API keys needed for structural changes). Preview via `file:///` path.
- Never push directly to `main`. Feature branch → staging → PR.

---

## Task 1: CSS — add `.status-strips` wrapper rules and `.status-strip-name`

**Files:**
- Modify: `style.css:426-434` (`.status-strip` block) and `style.css:463-466` (`.status-strip-text em` block)

**Step 1: Move `margin-bottom` from `.status-strip` to a new `.status-strips` wrapper rule**

In `style.css`, find the `.status-strip` rule (around line 426). Remove `margin-bottom: var(--space-3);` from it.

Before (the `.status-strip` block):
```css
.status-strip {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  padding: var(--space-3) var(--space-6);
  background: rgba(34, 197, 94, 0.04);
  border: 1px solid rgba(34, 197, 94, 0.18);
  border-left: 3px solid var(--accent-books);
  margin-bottom: var(--space-3);
}
```

After:
```css
.status-strip {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  padding: var(--space-3) var(--space-6);
  background: rgba(34, 197, 94, 0.04);
  border: 1px solid rgba(34, 197, 94, 0.18);
  border-left: 3px solid var(--accent-books);
}
```

**Step 2: Add `.status-strips` container rules above the `.status-strip` block**

Insert immediately before the `/* NOW READING — Status strip */` section comment:

```css
/* ──────────────────────────────────────────────
   STATUS STRIPS — container (stacked → side-by-side)
   ────────────────────────────────────────────── */

.status-strips {
  display: flex;
  flex-direction: column;
  gap: var(--space-3);
  margin-bottom: var(--space-3);
}
```

**Step 3: Add `.status-strip-name` colour rule after the `.status-strip-text em` block**

After the existing:
```css
.status-strip-text em {
  font-style: italic;
  color: var(--text-primary);
}
```

Add:
```css
.status-strip-name {
  color: var(--text-secondary);
}
```

**Step 4: Add desktop media query for side-by-side layout**

Find the `@media (min-width: 768px)` block in `style.css` (search for it — it's around line 980+). Add these rules inside it, grouped with other layout rules:

```css
  .status-strips {
    flex-direction: row;
    align-items: stretch;
  }

  .status-strips .status-strip {
    flex: 1;
  }
```

**Step 5: Commit**

```bash
git add style.css
git commit -m "feat(css): status-strips wrapper, status-strip-name colour rule"
```

---

## Task 2: Python — update `build_now_reading_html()` in `build.py`

**Files:**
- Modify: `build.py:238-251` (`build_now_reading_html` function)

**Step 1: Update single-book branch and docstring**

Find `build_now_reading_html` (around line 229). Change:

```python
def build_now_reading_html(books: list[dict]) -> str:
    """Generate status strip HTML for currently-reading shelf.

    0 books  → placeholder comment (section invisible)
    1 book   → "<em>Title</em> by Author"
    2+ books → "<em>Title 1</em>, <em>Title 2</em>"
    """
    if not books:
        return "            <!-- no books currently reading -->"
    if len(books) == 1:
        t = html.escape(books[0]["title"])
        a = html.escape(books[0]["author"])
        text = f"<em>{t}</em> by {a}"
    else:
        titles = ", ".join(f"<em>{html.escape(b['title'])}</em>" for b in books)
        text = titles
```

To:

```python
def build_now_reading_html(books: list[dict]) -> str:
    """Generate status strip HTML for currently-reading shelf.

    0 books  → placeholder comment (section invisible)
    1 book   → "<em>Title</em> <span class="status-strip-name">Author</span>"
    2+ books → "<em>Title 1</em>, <em>Title 2</em>" (titles only)
    """
    if not books:
        return "            <!-- no books currently reading -->"
    if len(books) == 1:
        t = html.escape(books[0]["title"])
        a = html.escape(books[0]["author"])
        text = f'<em>{t}</em> <span class="status-strip-name">{a}</span>'
    else:
        titles = ", ".join(f"<em>{html.escape(b['title'])}</em>" for b in books)
        text = titles
```

**Step 2: Commit**

```bash
git add build.py
git commit -m "feat(build): remove 'by' connector in now-reading strip"
```

---

## Task 3: HTML — wrap both strips in `.status-strips` container

**Files:**
- Modify: `index.html:1282-1300`

**Step 1: Add wrapper div**

Find this block (around line 1282):

```html
          <!-- ── NOW READING STATUS STRIP ── -->
<!-- goodreads-now:start -->
            <div class="status-strip">
              <span class="status-strip-label">Now reading</span>
              <span class="status-strip-sep">›</span>
              <span class="status-strip-text"><em>Stinkbug</em> by Sinéad Stubbins</span>
            </div>
<!-- goodreads-now:end -->
          <!-- ── NOW PLAYING STATUS STRIP ── -->
          <div id="now-playing-strip" class="status-strip status-strip--music" aria-live="polite" hidden>
            <span class="status-strip-label" id="now-playing-label">Now playing</span>
            <span class="waveform" aria-hidden="true">
              <span class="waveform-bar"></span>
              <span class="waveform-bar"></span>
              <span class="waveform-bar"></span>
            </span>
            <span class="status-strip-sep">›</span>
            <span class="status-strip-text" id="now-playing-text"></span>
          </div>
```

Replace with (wrapper div added, indentation unchanged inside markers):

```html
          <!-- ── STATUS STRIPS ── -->
          <div class="status-strips">
<!-- goodreads-now:start -->
            <div class="status-strip">
              <span class="status-strip-label">Now reading</span>
              <span class="status-strip-sep">›</span>
              <span class="status-strip-text"><em>Stinkbug</em> by Sinéad Stubbins</span>
            </div>
<!-- goodreads-now:end -->
          <div id="now-playing-strip" class="status-strip status-strip--music" aria-live="polite" hidden>
            <span class="status-strip-label" id="now-playing-label">Now playing</span>
            <span class="waveform" aria-hidden="true">
              <span class="waveform-bar"></span>
              <span class="waveform-bar"></span>
              <span class="waveform-bar"></span>
            </span>
            <span class="status-strip-sep">›</span>
            <span class="status-strip-text" id="now-playing-text"></span>
          </div>
          </div><!-- /.status-strips -->
```

> **Note on the `goodreads-now` marker:** The markers must stay flush-left (no leading spaces) — do NOT indent them. The content between them (the `<div class="status-strip">`) is what gets replaced by the build script. The wrapper `<div class="status-strips">` is outside the markers and survives all builds.

**Step 2: Commit**

```bash
git add index.html
git commit -m "feat(html): wrap status strips in .status-strips container"
```

---

## Task 4: HTML — update now-playing JS to use DOM spans

**Files:**
- Modify: `index.html` — the minified now-playing IIFE (around line 1587, after `<!-- jsonld:end -->`)

**Step 1: Find the now-playing script**

Search for `WORKER=` in `index.html`. It will be a single-line minified `<script>` tag containing the IIFE. The relevant section reads:

```js
text.textContent=d.track+' by '+d.artist;
```

**Step 2: Replace that assignment with DOM manipulation**

Change:
```js
text.textContent=d.track+' by '+d.artist;
```

To:
```js
text.innerHTML='';var em=document.createElement('em');em.textContent=d.track;text.appendChild(em);text.appendChild(document.createTextNode(' '));var sp=document.createElement('span');sp.className='status-strip-name';sp.textContent=d.artist;text.appendChild(sp);
```

This:
1. Clears the existing text node
2. Creates `<em>track name</em>` (using `textContent` — safe, no injection risk)
3. Adds a space text node between em and span
4. Creates `<span class="status-strip-name">artist name</span>`

**Step 3: Commit**

```bash
git add index.html
git commit -m "feat(js): now-playing strip uses spans for track/artist contrast"
```

---

## Task 5: Local build and visual check

**Step 1: Run build without API keys**

```bash
python3 build.py
```

Expected output: warnings about missing env vars (normal), but no Python errors. The `goodreads-now` strip will inject `<!-- no books currently reading -->` placeholder since there's no Goodreads API key locally.

**Step 2: Open the local file**

Open `file:///Users/nicholassheehan/Documents/Claude%20Files/Personal%20website/index.html` in a browser.

**What to check:**
- The now-playing strip is hidden (expected — no live data locally)
- The now-reading strip is also hidden (placeholder comment, normal)
- No layout regressions in the panel grid below
- Resize to desktop width (≥768px) — strips area should look correct even when empty
- Open browser DevTools, temporarily remove `hidden` from `#now-playing-strip` and check it renders with the `.status-strips` wrapper side-by-side when also visible with the reading strip

**Step 3: Confirm with user before pushing to staging**

---

## Task 6: Push to staging and verify with real data

> Only proceed after user confirms local preview looks good.

**Step 1: Prepare and push**

```bash
git restore og-image.png sitemap.xml
git pull --rebase origin main
git push origin main:staging
```

**Step 2: Wait for CI, then pull staging**

```bash
git fetch origin staging
git checkout staging
git pull origin staging
```

Open `file:///Users/nicholassheehan/Documents/Claude%20Files/Personal%20website/index.html`.

**What to check on staging (real API data):**
- Now-reading strip shows `<em>Title</em> Artist` (no "by") — author in grey
- Now-playing strip shows track in italic white, artist in grey (visible after ~5s for Worker fetch)
- On desktop: both visible strips sit side-by-side
- On mobile (or narrow viewport): strips stack vertically
- When only one strip is visible, it fills full width

**Step 3: Switch back to main and confirm**

```bash
git checkout main
```

---

## Task 7: PR staging → main

```bash
git restore og-image.png sitemap.xml
```

Open a PR from `staging` → `main` via GitHub. Title: `feat: iteration 13 — status strip polish`. The CI build on main will deploy to production.

After merge, update:
1. `docs/roadmap.md` — mark iteration 13 ✅
2. `MEMORY.md` — update Design section to reflect `.status-strips` wrapper, `.status-strip-name`, and removal of "by" connector
