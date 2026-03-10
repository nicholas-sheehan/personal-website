# Iteration 14 — Visual & Data Polish: Design

**Date:** 2026-03-10
**Status:** Approved

## Overview

A batch of small fixes addressing visual inconsistencies, missing data, and code quality issues identified in a full design + technical review. No new infrastructure. Four change groups: CSS, static HTML, build.py, and JS.

---

## Group 1: Typography & CSS (style.css)

- `.track-title`: `font-weight: 500` → `400` (matches books, films, articles)
- `.article-title`: `font-size: 0.75rem` → `0.78rem` (matches all other panel primary titles)
- Modal `max-height: calc(100vh - 4rem)` → `calc(100dvh - 4rem)` (prevents modal extending behind mobile browser chrome)
- Add `:focus-visible` outline to `.panel-footer-link` matching existing interactive element pattern (`1px solid var(--accent)`, `outline-offset: 2px`)
- Google Fonts URL: restrict weight axis from `100..800` to `ital,wght@0,400;0,700;1,400` — removes unused weights after the 500→400 fix above; reduces font payload
- Add `.status-strip-title { color: var(--text-primary); }` — for the now-playing track title span (Group 4)

---

## Group 2: Static HTML (index.html — outside markers)

- **Panel reorder**: swap Music and Films in the 2×2 grid so order is Books | Music (top row) / Films | Articles (bottom row). On desktop, Music sits directly below the now-playing status strip — consistent purple column.
- **Avatar dimensions**: `width="96" height="96"` → `width="72" height="72"` to match CSS rendered size; eliminates layout shift before CSS loads
- **Articles footer**: add `<footer class="panel-footer"><a class="panel-footer-link" href="https://www.instapaper.com/starred" target="_blank" rel="noopener noreferrer">→ Instapaper</a></footer>` after `<!-- articles:end -->`, matching Books/Films/Music pattern

---

## Group 3: Build.py

- **Goodreads UTM stripping**: apply `_strip_tracking_params()` to book URLs in `fetch_goodreads()` — same fix already applied to Instapaper in iteration 2; removes `?utm_medium=api&utm_source=rss` from modal "View on Goodreads" links
- **Films watched date**: extract `pubDate` from Letterboxd RSS entries (RFC 2822), format as "Watched Month Year", add as `data-watched` attribute on film `.panel-row` elements; displayed in modal `metaPersonal` line (alongside director in `metaSource`), matching "Finished Month Year" pattern for books
- **`article-source` element**: change `build_articles_html()` to output `<div class="article-source">` instead of `<span class="article-source">` — matches `.book-author`, `.film-year`, `.track-artist`; removes the `display: inline-block` and `align-self: flex-start` CSS workarounds
- **Section source subtitles**: standardise to "on [Service]" — `build_gravatar_*` and static HTML: "via Goodreads" → "on Goodreads", "via Last.fm" → "on Last.fm", "saved in Instapaper" → "on Instapaper"; "on Letterboxd" already correct

---

## Group 4: JavaScript (index.html — outside markers)

- **Now-playing track title**: change `document.createElement('em')` → `document.createElement('span')` with `className = 'status-strip-title'`; removes italic (track titles aren't conventionally italicised unlike book titles); CSS class provides `color: var(--text-primary)` (added in Group 1)
- **Modal link hidden state**: when `url === '#'` (no URL on row), set `linkEl.hidden = true`; matches existing pattern for `descEl` and `metaPersonalEl`; prevents empty clickable `<a>` rendering

---

## Files changed

| File | Group |
|------|-------|
| `style.css` | 1 |
| `index.html` (static HTML) | 2, 4 |
| `build.py` | 3 |

---

## Roadmap items to add (not in this iteration)

From the technical review — to be added to `docs/roadmap.md` dev environment section:
- Pin `requirements.txt` versions
- API keys as request headers for TMDB and Last.fm (not URL params)
- Wrangler deploy step in CI
- HTML validation step in CI
- OG image: skip regeneration if Gravatar data unchanged
- Boot sequence: `sessionStorage` skip for returning visitors
- CI deploy job: use artifact handoff instead of second `git pull`
- CI deploy job: add concurrency control
