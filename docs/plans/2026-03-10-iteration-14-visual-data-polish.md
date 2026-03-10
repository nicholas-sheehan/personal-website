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

**Step 6: Add `.status-strip-title` CSS class**

Find `.status-strip-name` (around line 478). Add `.status-strip-title` immediately after it:

```css
.status-strip-name {
  color: var(--text-secondary);
}

.status-strip-title {
  color: var(--text-primary);
}
```

**Step 7: Commit**

```bash
git add style.css
git commit -m "fix(css): track-title weight, article-title size, article-source block, modal dvh, focus-visible, status-strip-title"
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

**Step 5: Commit**

```bash
git add build.py
git commit -m "feat(build): strip Goodreads UTM params, film watched date, article-source div"
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

**Step 4: Commit**

```bash
git add index.html
git commit -m "fix(js): now-playing track not italic, film watched date in modal, hide modal link when no url"
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
- Click a film row → modal shows `data-watched` value (will be populated after real build on staging)
- Click an article row → modal link is hidden if row has no URL (all current rows have URLs so test by temporarily removing `data-url` from one in DevTools)

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
