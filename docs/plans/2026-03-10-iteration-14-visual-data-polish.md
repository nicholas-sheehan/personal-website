# Iteration 14 — Visual & Data Polish Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Batch of small CSS, HTML, build-script, and JS fixes addressing visual inconsistencies, missing data, and code quality issues found in a full design review.

**Architecture:** Four separate file-level tasks (style.css, build.py, index.html static, index.html JS), each committed independently. No new data sources or infrastructure.

**Tech Stack:** CSS, Python, vanilla JS, Letterboxd RSS (`pubDate` field), Goodreads URL stripping.

---

## Context

This is a static personal website. Key facts for implementers:
- `style.css` is the CSS **source** — it gets inlined at build time between `<!-- style:start/end -->` markers in `index.html`. Edit `style.css`; the build inlines it. Do NOT edit the `<style>` block in `index.html` directly.
- `index.html` has content injection markers (`<!-- tag:start/end -->`). Static HTML **outside** markers survives builds. Static HTML **between** markers gets overwritten by `build.py`.
- The now-playing `<script>` at the bottom of `index.html` is outside all markers and survives builds.
- Local build: `python3 build.py` (no API keys needed for structural changes). Preview via `file:///` path.
- Never push directly to `main`. Feature branch → staging → PR.

Work from: `/Users/nicholassheehan/Documents/Claude Files/Personal website`

---

## Task 1: CSS fixes (style.css)

**Files:**
- Modify: `style.css`

**Step 1: Fix `.track-title` font-weight**

Find `.track-title` (around line 798). Change `font-weight: 500` to `font-weight: 400`:

```css
.track-title {
  font-family: var(--font-mono);
  font-size: 0.78rem;
  font-weight: 400;   /* was 500 */
  color: var(--text-primary);
  line-height: 1.4;
  text-shadow: 0 0 6px rgba(180, 210, 255, 0.12);
}
```

**Step 2: Fix `.article-title` font-size**

Find `.article-title` (around line 832). Change `font-size: 0.75rem` to `font-size: 0.78rem`:

```css
.article-title {
  font-family: var(--font-mono);
  font-size: 0.78rem;   /* was 0.75rem */
  font-weight: 400;
  color: var(--text-primary);
  line-height: 1.45;
  text-shadow: 0 0 6px rgba(180, 210, 255, 0.12);
}
```

**Step 3: Fix `.article-source` — remove `display: inline-block` workaround**

`build.py` will be updated (Task 2) to output `<div class="article-source">` instead of `<span>`. A `<div>` is already block-level, so `display: inline-block` is no longer needed.

Find `.article-source` (around line 842). Remove `display: inline-block`:

```css
.article-source {
  font-family: var(--font-mono);
  font-size: 0.6rem;
  font-weight: 400;
  color: var(--accent-articles);
  background: rgba(59, 130, 246, 0.07);
  border: 1px solid rgba(59, 130, 246, 0.18);
  padding: 0.1rem 0.35rem;
  margin-top: 0.25rem;
  letter-spacing: 0.03em;
  white-space: nowrap;
}
```

Also find the `@media (min-width: 768px)` block and remove the `.article-source` override inside it (around line 947):

```css
/* REMOVE THIS BLOCK entirely: */
  .article-source {
    margin-top: 0;
    flex-shrink: 0;
    align-self: flex-start;
  }
```

This `align-self: flex-start` was only needed because `<span>` is an inline element competing in a flex row. A `<div>` behaves correctly without it.

**Step 4: Fix modal `max-height` to use `dvh`**

Find `max-height: calc(100vh - 4rem)` in the `.modal-box` rule (around line 1065). Change `100vh` to `100dvh`:

```css
max-height: calc(100dvh - 4rem);
```

**Step 5: Add `:focus-visible` to `.panel-footer-link`**

Find `.panel-footer-link:hover` (around line 627). Add a `:focus-visible` rule immediately after it:

```css
.panel-footer-link:focus-visible {
  outline: 1px solid var(--accent);
  outline-offset: 2px;
}
```

**Step 6: Add `.status-strip-title` CSS class (with link states)**

Find `.status-strip-name` (around line 478). Add `.status-strip-title` immediately after it, including link hover state for when the strip is clickable:

```css
.status-strip-name {
  color: var(--text-secondary);
}

.status-strip-title {
  color: var(--text-primary);
}

.status-strip-title[href] {
  text-decoration: none;
}

.status-strip-title[href]:hover {
  color: var(--accent);
}
```

**Step 7: Add `.modal-desc-label` CSS class**

Find `.modal-desc` (around line 1090). Add `.modal-desc-label` immediately before it:

```css
.modal-desc-label {
  display: block;
  font-size: 0.6rem;
  font-weight: 400;
  color: var(--text-secondary);
  letter-spacing: 0.08em;
  text-transform: uppercase;
  margin-bottom: 0.35rem;
}
```

**Step 8: Commit**

```bash
git add style.css
git commit -m "fix(css): track-title weight, article-title size, article-source block, modal dvh, focus-visible, status-strip-title, modal-desc-label"
```

---

## Task 2: Build.py fixes

**Files:**
- Modify: `build.py`

**Step 1: Strip UTM params from Goodreads URLs**

In `fetch_goodreads()`, find the `url` assignment (around line 166):

```python
url = link_el.text.strip() if link_el is not None and link_el.text else ""
```

Change to:

```python
url = _strip_tracking_params(link_el.text.strip()) if link_el is not None and link_el.text else ""
```

`_strip_tracking_params()` is already defined at line 706 and removes `utm_source`, `utm_medium`, etc. This removes `?utm_medium=api&utm_source=rss` from Goodreads modal links.

**Step 2: Extract watched date from Letterboxd RSS**

In `fetch_letterboxd()`, find the `films.append(...)` block (around line 285). Before it, add `pubDate` extraction:

Find this block:
```python
        link_el = item.find("link")
        url = link_el.text.strip() if link_el is not None and link_el.text else "#"

        films.append({"title": title, "year": year, "rating": rating, "url": url})
```

Change to:
```python
        link_el = item.find("link")
        url = link_el.text.strip() if link_el is not None and link_el.text else "#"

        # Watched date from pubDate (RFC 2822)
        watched = ""
        pub_el = item.find("pubDate")
        if pub_el is not None and pub_el.text:
            parsed = parsedate(pub_el.text.strip())
            if parsed:
                try:
                    watched = datetime(parsed[0], parsed[1], parsed[2]).strftime("Watched %B %Y")
                except Exception:
                    pass

        films.append({"title": title, "year": year, "rating": rating, "url": url, "watched": watched})
```

Also update the docstring at line 262 to mention `watched`:

```python
def fetch_letterboxd(rss_url: str, limit: int) -> list[dict]:
    """Return a list of {title, year, rating, url, watched} dicts from the RSS feed."""
```

**Step 3: Add `data-watched` to `build_film_html()`**

In `build_film_html()`, find where data attrs are built (around line 379). Add `data-watched` after `data-synopsis`:

```python
        if film.get("synopsis"):
            data += f' data-synopsis="{html.escape(film["synopsis"], quote=True)}"'
        if film.get("watched"):
            data += f' data-watched="{html.escape(film["watched"], quote=True)}"'
```

**Step 4: Change `article-source` from `<span>` to `<div>` in `build_article_html()`**

In `build_article_html()`, find line 758:

```python
        source_html = f'\n                    <span class="article-source">{html.escape(domain)}</span>' if domain else ""
```

Change `span` to `div`:

```python
        source_html = f'\n                    <div class="article-source">{html.escape(domain)}</div>' if domain else ""
```

**Step 5: Make now-reading strip clickable**

In `build_now_reading_html()`, update the title HTML to wrap in `<a>` when a URL is available. Replace the current single-book and multi-book text assembly:

Find:
```python
    if len(books) == 1:
        t = html.escape(books[0]["title"])
        a = html.escape(books[0]["author"])
        text = f'<em>{t}</em> <span class="status-strip-name">{a}</span>'
    else:
        titles = ", ".join(f"<em>{html.escape(b['title'])}</em>" for b in books)
        text = titles
```

Change to:
```python
    def _title_link(b: dict) -> str:
        t = html.escape(b["title"])
        u = html.escape(b.get("url", ""), quote=True)
        if u:
            return f'<a class="status-strip-title" href="{u}" target="_blank" rel="noopener noreferrer">{t}</a>'
        return f'<span class="status-strip-title">{t}</span>'

    if len(books) == 1:
        a = html.escape(books[0]["author"])
        text = f'{_title_link(books[0])} <span class="status-strip-name">{a}</span>'
    else:
        text = ", ".join(_title_link(b) for b in books)
```

Also remove the `<em>` wrapping from any existing fallback text — titles now use `.status-strip-title` class rather than `<em>`.

**Step 6: Commit**

```bash
git add build.py
git commit -m "feat(build): strip Goodreads UTM params, film watched date, article-source div, now-reading clickable"
```

---

## Task 3: Static HTML fixes (index.html — outside markers)

**Files:**
- Modify: `index.html`

> **IMPORTANT:** All changes in this task are to static HTML **outside** `<!-- tag:start/end -->` markers. They survive builds. Do NOT edit anything between marker pairs.

**Step 1: Restrict Google Fonts weight axis**

Find line 20:

```html
  <link href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:ital,wght@0,100..800;1,100..800&display=swap" rel="stylesheet">
```

Change to (only weights 400, 700 regular and 400 italic — all that are used):

```html
  <link href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:ital,wght@0,400;0,700;1,400&display=swap" rel="stylesheet">
```

**Step 2: Fix section source subtitles**

Make three changes to the section source `<p>` tags:

1. Line ~1347: `via Goodreads` → `on Goodreads`
2. Line ~1463: `via Last.fm` → `on Last.fm`
3. Line ~1522: `saved in Instapaper` → `on Instapaper`

"on Letterboxd" (line ~1405) is already correct — leave it unchanged.

**Step 3: Fix avatar dimensions**

Find the avatar `<img>` (around line 1273):

```html
<img class="avatar" src="..." width="96" height="96" ...>
```

Change `width="96" height="96"` to `width="72" height="72"` to match the CSS rendered size.

**Step 4: Reorder panels — Music before Films**

The current panel order in the HTML is: Books → Films → Music → Articles.
New order: Books → Music → Films → Articles.

Find and cut the entire Music `<section>` block — from `<!-- MUSIC -->` comment to and including its closing `</section>` tag (approximately lines 1458–1515 in the current file).

Paste it immediately before the `<!-- FILMS -->` comment (currently around line 1400).

The result should be:
```
Books section
Music section   ← moved up
Films section   ← moved down
Articles section
```

**Step 5: Add Articles panel footer link**

Find `<!-- instapaper:end -->` (around line 1563). After the closing `</div>` of `.panel-body` and before the closing `</section>`, add the footer:

The current ending of the Articles section:
```html
<!-- instapaper:end -->
              </div>
            </section>
```

Change to:
```html
<!-- instapaper:end -->
              </div>
              <footer class="panel-footer">
                <a href="https://www.instapaper.com/starred" class="panel-footer-link" target="_blank" rel="noopener noreferrer">→ Instapaper</a>
              </footer>
            </section>
```

**Step 6: Commit**

```bash
git add index.html
git commit -m "fix(html): panel reorder (music second), avatar dims, articles footer, subtitle text, font weights"
```

---

## Task 4: JavaScript fixes (index.html — outside markers)

**Files:**
- Modify: `index.html` (two separate scripts)

> Both scripts are outside all markers and survive builds.

**Step 1: Fix now-playing track title — remove italic**

Find the now-playing IIFE (search for `WORKER=` in `index.html`). Inside it, find:

```js
text.innerHTML='';var em=document.createElement('em');em.textContent=d.track;text.appendChild(em);
```

Change `em` element to a `span` with class `status-strip-title`:

```js
text.innerHTML='';var tk=document.createElement('span');tk.className='status-strip-title';tk.textContent=d.track;text.appendChild(tk);
```

The full replacement in context (just the track creation part changes — artist span and rest of update() function stay identical):

Old:
```js
text.innerHTML='';var em=document.createElement('em');em.textContent=d.track;text.appendChild(em);text.appendChild(document.createTextNode(' '));var sp=document.createElement('span');sp.className='status-strip-name';sp.textContent=d.artist;text.appendChild(sp);
```

New:
```js
text.innerHTML='';var tk=document.createElement('span');tk.className='status-strip-title';tk.textContent=d.track;text.appendChild(tk);text.appendChild(document.createTextNode(' '));var sp=document.createElement('span');sp.className='status-strip-name';sp.textContent=d.artist;text.appendChild(sp);
```

**Step 2: Add films watched date to modal**

Find the modal IIFE (search for `openModal` in `index.html`). Inside `openModal()`, find the `film` branch (around line 1715):

```js
            } else if (type === 'film') {
              var director = row.dataset.director ? 'dir. ' + row.dataset.director : '';
              var filmSourceParts = [row.dataset.year, director].filter(Boolean);
              metaSource = filmSourceParts.join(' · ');
              metaPersonal = row.dataset.stars || '';
              desc = row.dataset.synopsis || '';
              linkText = '→ View on Letterboxd';
```

Change to include watched date in `metaPersonal`:

```js
            } else if (type === 'film') {
              var director = row.dataset.director ? 'dir. ' + row.dataset.director : '';
              var filmSourceParts = [row.dataset.year, director].filter(Boolean);
              metaSource = filmSourceParts.join(' · ');
              var filmPersonalParts = [row.dataset.stars, row.dataset.watched].filter(Boolean);
              metaPersonal = filmPersonalParts.join(' · ');
              desc = row.dataset.synopsis || '';
              linkText = '→ View on Letterboxd';
```

**Step 3: Fix modal link hidden state**

Still in the modal IIFE, find (around line 1751):

```js
            linkEl.textContent = linkText;
            linkEl.href = url;
```

Change to hide the link when there's no real URL:

```js
            if (url === '#') {
              linkEl.hidden = true;
            } else {
              linkEl.textContent = linkText;
              linkEl.href = url;
              linkEl.hidden = false;
            }
```

**Step 4: Add modal description labels**

Still in the modal IIFE, find where `desc` is assigned per type (the `if/else if` block computing `metaSource`, `metaPersonal`, `desc`). After the block, add a `descLabel` variable:

```js
            var descLabel = '';
            if (type === 'book')    descLabel = desc ? 'Review' : '';
            if (type === 'film')    descLabel = desc ? 'Synopsis' : '';
            if (type === 'music')   descLabel = desc ? 'Artist bio' : '';
            if (type === 'article') descLabel = desc ? 'Excerpt' : '';
```

Then find where the modal description element is populated (search for `modal-desc` or where `desc` text is set). Change it to prepend the label when present:

```js
            var descEl = modal.querySelector('.modal-desc');
            if (descLabel) {
              descEl.innerHTML = '<span class="modal-desc-label">' + descLabel + '</span>' + desc;
            } else {
              descEl.textContent = desc;
            }
```

Note: `descLabel` is safe to use as a literal string (hardcoded per type — no user input). `desc` comes from `data-*` attributes which are HTML-escaped by `build.py` via `html.escape(..., quote=True)`. Setting `.innerHTML` here is safe.

**Step 5: Make now-playing strip clickable**

Find the now-playing IIFE (the `tk` span created in Step 1). Change the track node to an `<a>` when a URL is available:

Old (after Step 1):
```js
text.innerHTML='';var tk=document.createElement('span');tk.className='status-strip-title';tk.textContent=d.track;text.appendChild(tk);
```

New:
```js
text.innerHTML='';var tk=d.url?document.createElement('a'):document.createElement('span');tk.className='status-strip-title';tk.textContent=d.track;if(d.url){tk.href=d.url;tk.target='_blank';tk.rel='noopener noreferrer';}text.appendChild(tk);
```

Note: `d.url` will be `null` until the worker is updated (Task 4b below) — the fallback to `<span>` ensures this is safe to deploy now.

**Step 6: Commit**

```bash
git add index.html
git commit -m "fix(js): now-playing track not italic, film watched date in modal, hide modal link when no url, modal desc labels, now-playing clickable"
```

---

## Task 4b: Worker update — expose track URL

**Files:**
- Modify: `worker/index.js`

**Step 1: Add `url` to worker response**

Find the `return cors(Response.json({...}))` block (line 17). Add `url`:

```js
    return cors(Response.json({
      nowPlaying: track["@attr"]?.nowplaying === "true",
      track:  track.name,
      artist: track.artist["#text"],
      url:    track.url || null,
    }));
```

**Step 2: Deploy worker**

```bash
cd worker && wrangler deploy
```

Expected output: `Deployed now-playing ... (X sec)`.

**Step 3: Commit**

```bash
git add worker/index.js
git commit -m "feat(worker): expose Last.fm track URL for clickable now-playing strip"
```

---

## Task 5: Local build and visual check

**Step 1: Run build**

```bash
python3 build.py
```

Expected: warnings about missing env vars (TMDB, Instapaper, Last.fm) — normal locally. No Python errors. `style.css` inlined. Goodreads data injected.

**Step 2: Open local file**

Open `file:///Users/nicholassheehan/Documents/Claude%20Files/Personal%20website/index.html`

**What to verify:**
- Panel order is now: Books | Music (top row) / Films | Articles (bottom row)
- Track titles in Music panel are same weight as book/film titles (not bolder)
- Article titles match size of other panel titles
- Articles panel has `→ Instapaper` footer link
- Section subtitles all say "on [Service]" (not "via" or "saved in")
- Now-playing strip: if visible, track title is NOT italic
- Now-reading strip: book title is a clickable link (hover → accent colour)
- Click a film row → modal shows `data-watched` value (will be populated after real build on staging)
- Click an article row → modal link is hidden if row has no URL (all current rows have URLs so test by temporarily removing `data-url` from one in DevTools)
- Click any panel row with a description → modal shows a small uppercase label above the description text ("Review", "Synopsis", "Artist bio", "Excerpt")

**Step 3: Confirm with user before pushing to staging**

---

## Task 6: Push to staging

> Only proceed after user confirms local preview.

```bash
git restore og-image.png sitemap.xml
git pull --rebase origin main
git push --force origin main:staging
```

Wait for CI to complete on staging. Pull staging:

```bash
git fetch origin staging && git checkout staging && git reset --hard origin/staging
```

Open local file and verify:
- Films modal shows "Watched Month Year" in the personal meta line
- Article-source domains are `<div>` elements (inspect in DevTools — should render as block, not inline)
- Now-playing track title is not italic (visible when scrobbling — CORS means this only works in production)
- Now-playing track title is a clickable link when scrobbling (worker URL now included)
- Modal description labels appear ("Synopsis", "Review", etc.) when a description exists

---

## Task 7: PR and docs

```bash
git checkout main
git restore og-image.png sitemap.xml
```

Open PR from `staging` → `main`. Title: `fix: iteration 14 — visual and data polish`.

After merge, update:
1. `docs/roadmap.md` — mark iteration 14 ✅
2. `MEMORY.md` — update Design section: note panel order (Books | Music / Films | Articles), `.status-strip-title` class, section subtitles standardised to "on [Service]"
