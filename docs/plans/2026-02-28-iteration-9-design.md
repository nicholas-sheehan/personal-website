# Iteration 9 — Item Detail Modal: Design Document

**Date:** 2026-02-28
**Status:** Approved, ready for implementation planning

---

## Overview

Add click-to-expand modal overlays to all four content panels (Books, Films, Music, Articles). Each panel row becomes interactive: clicking it opens a Y2K-styled modal showing richer data about that item. Modal dismiss via ESC, backdrop click, or `[ X ]` button.

This is the first real JS interactivity on the site (beyond analytics, timestamp localisation, boot sequence, and the Snake easter egg).

---

## Architecture

**Approach:** Data-attributes + inline script.

- `build.py` injects `data-*` attrs with richer data onto each `.panel-row` at build time
- A new inline `<script>` block (at bottom of `<body>`, separate from existing inline scripts) drives all modal behavior
- One static modal element in `index.html`, hidden by default, populated by JS from data attrs
- CSS in `style.css`

No external JS files, no runtime API calls. Fully static.

---

## Data Layer (build.py changes)

Each `build_*_html()` function adds `role="button" tabindex="0"` and `data-*` attrs to `.panel-row` elements.

### Books (Goodreads RSS — no new APIs)
Goodreads RSS already includes these fields; we're just not currently reading them.

| Attr | Source | Notes |
|------|--------|-------|
| `data-modal-type="book"` | static | |
| `data-title` | already extracted | |
| `data-author` | already extracted | |
| `data-stars` | already extracted (`rating` int) | e.g. `"4"` |
| `data-cover` | `<book_image_url>` RSS field | Omit if empty |
| `data-description` | `<book_description>` RSS field | Truncate to 400 chars in build.py |
| `data-url` | `<link>` RSS field | Goodreads book page |

### Films (Letterboxd RSS + TMDB API — new API)
Letterboxd URL already fetched. TMDB adds poster, director, synopsis.

| Attr | Source | Notes |
|------|--------|-------|
| `data-modal-type="film"` | static | |
| `data-title` | already extracted | |
| `data-year` | already extracted | |
| `data-stars` | already extracted | |
| `data-url` | already extracted (Letterboxd review URL) | |
| `data-poster` | TMDB `search/movie` → `poster_path` | `https://image.tmdb.org/t/p/w300{path}`. Omit if no result. |
| `data-director` | TMDB `movie/{id}/credits` → crew where `job=="Director"` | First director only. Omit if not found. |
| `data-synopsis` | TMDB `overview` | Truncate to 400 chars |

TMDB flow per film: `search/movie?query={title}&year={year}` → get `id` + `poster_path` + `overview` → `movie/{id}/credits` → extract director. Two HTTP calls per film (10 total). Wrapped in `try/except`; on failure, TMDB attrs are omitted (modal still renders with Letterboxd data).

**New secret required:** `TMDB_API_KEY` (added to GitHub Actions workflow + repo secrets).

### Music (Last.fm — 2 new API call types)
Top tracks API already returns a `url` field; we're not currently extracting it.

| Attr | Source | Notes |
|------|--------|-------|
| `data-modal-type="music"` | static | |
| `data-title` | already extracted | |
| `data-artist` | already extracted | |
| `data-plays` | already extracted | |
| `data-url` | `url` field in top tracks API response | |
| `data-album` | `track.getInfo` API | 1 call per track (5 total). Omit if missing. |
| `data-bio` | `artist.getInfo` API | Deduplicated by artist name (max 5 unique). Truncate to 300 chars. Strip HTML tags from bio. |

### Articles (Instapaper — no new APIs)
Instapaper bookmarks/list endpoint already returns `description`; we're not currently using it.

| Attr | Source | Notes |
|------|--------|-------|
| `data-modal-type="article"` | static | |
| `data-title` | already extracted | |
| `data-url` | already extracted | |
| `data-source` | domain extracted from URL | Already computed for display; just also store as attr |
| `data-description` | `description` field from Instapaper API | Truncate to 400 chars. Omit if empty. |

---

## Row Interaction Model

All `.panel-row` elements gain:

```html
<div class="panel-row" role="button" tabindex="0"
     data-modal-type="book"
     data-title="..." data-author="..." ...>
  <!-- existing content unchanged -->
</div>
```

**Article rows:** Currently wrap content in `<a href>`. That inner `<a>` is removed — the row becomes the trigger. The outbound link moves inside the modal. Visual appearance is identical (title + source domain still shown).

CSS: `cursor: pointer` and a subtle hover state on `.panel-row[role="button"]`. The existing `panel--articles .panel-row:hover` rule generalises to cover all four panels.

---

## Modal HTML Structure

One static element at the bottom of `<body>`, before `</body>`:

```html
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
        <p class="modal-desc"></p>
        <a class="modal-link" target="_blank" rel="noopener noreferrer"></a>
      </div>
    </div>
  </div>
</div>
```

**Header band:** Matches `.panel-header` rhythm.
- Left: `[ X ]` close button + type label (e.g. `[▓] BOOKS`)
- Right: dim item index (e.g. `01 / 05`)
- `border-bottom: 1px solid var(--border)`

**`.modal-type-label`** values per type: `[▓] BOOKS`, `[▶] FILMS`, `[♫] MUSIC`, `[≡] ARTICLES`

---

## CSS

All new rules added to `style.css`.

### Modal overlay
```css
.modal-overlay {
  position: fixed; inset: 0; z-index: 200;
  display: flex; align-items: center; justify-content: center;
  background: rgba(5, 10, 20, 0.85);
  padding: var(--space-4);
}
@supports (backdrop-filter: blur(1px)) {
  .modal-overlay { backdrop-filter: blur(2px); }
}
@media (prefers-reduced-motion: no-preference) {
  .modal-overlay { animation: modal-fade 0.15s ease; }
}
```

### Modal box
```css
.modal-box {
  background: var(--panel);
  border-top: 4px solid var(--modal-accent, var(--accent));
  max-width: 400px; width: 100%;
  font-family: var(--font-mono);
}
/* Accent colour per type, driven by data-modal-type on .modal-box */
.modal-box[data-modal-type="book"]    { --modal-accent: #22c55e; }
.modal-box[data-modal-type="film"]    { --modal-accent: #f59e0b; }
.modal-box[data-modal-type="music"]   { --modal-accent: #a855f7; }
.modal-box[data-modal-type="article"] { --modal-accent: #3b82f6; }
```

### Modal content layout
- `.modal-content`: flex row, gap `var(--space-4)`
- `.modal-cover`: width 80px (64px for music), `object-fit: cover`, `max-height: 120px`; hidden when `src` is empty
- `.modal-body`: flex-1
- `.modal-title`: Y2K accent colour, same `text-shadow` phosphor glow as `.book-title`
- `.modal-meta`: `var(--text-secondary)`, `font-size: 0.75rem`
- `.modal-desc`: `var(--text-tertiary)`, `font-size: 0.7rem`, `-webkit-line-clamp: 4`, `display: -webkit-box`, `-webkit-box-orient: vertical`, `overflow: hidden`
- `.modal-link`: matches `.panel-footer-link` exactly — `var(--text-tertiary)`, `font-size: 0.6rem`, `letter-spacing: 0.06em`; hover shifts to `var(--text-secondary)`

### Close button
```css
.modal-close {
  background: none; border: none; cursor: pointer;
  color: var(--text-tertiary); font-family: var(--font-mono);
  font-size: 0.75rem;
}
.modal-close:hover { color: var(--text-primary); }
```

---

## JS Behavior

New inline `<script>` block at bottom of `<body>`, after existing inline scripts.

### Open
1. User clicks `.panel-row[role="button"]` (or presses Enter/Space while focused on one)
2. Collect all `.panel-row[role="button"]` in same panel to determine index (e.g. `02 / 05`)
3. Set `data-modal-type` on `.modal-box` (drives CSS accent colour + type label text)
4. Populate `.modal-type-label`, `.modal-index`, `.modal-title`, `.modal-meta`, `.modal-desc`, `.modal-link`
5. Show/hide `.modal-cover` based on `data-cover` / `data-poster`
6. Remove `hidden` from `#detail-modal`
7. Add `overflow: hidden` to `<body>`
8. Move focus to `.modal-close`
9. Store reference to the triggering row for focus-return on close

### Modal content per type
| Type | Title | Meta | Desc | Link text |
|------|-------|------|------|-----------|
| book | title | author · ★★★★ | description | `→ View on Goodreads` |
| film | title | year · ★★★½ · dir. Name | synopsis | `→ View on Letterboxd` |
| music | track title | artist · album · N plays | artist bio | `→ Listen on Last.fm` |
| article | title | source domain | description | `→ Read on [domain]` |

If optional fields (cover, description, bio, director, etc.) are absent, those elements are hidden — not shown empty.

### Close
- Backdrop click (`.modal-overlay`, not `.modal-box`), `.modal-close` click, or ESC key
- Add `hidden` to `#detail-modal`
- Remove `overflow: hidden` from `<body>`
- Return focus to the row that triggered the modal

### Keyboard (basic)
- Tab while modal open: cycles between `.modal-close` and `.modal-link` (two focusable elements)

---

## Files Changed

| File | Change |
|------|--------|
| `build.py` | `fetch_goodreads`: extract `book_image_url`, `book_description`, `link`; `build_book_html`: add data attrs |
| `build.py` | `fetch_letterboxd`: already extracts `url`; add `fetch_tmdb_data(title, year, api_key)` helper |
| `build.py` | `build_film_html`: add data attrs incl. TMDB fields |
| `build.py` | `fetch_lastfm_top_tracks`: extract `url` field; add `fetch_lastfm_track_info` + `fetch_lastfm_artist_info` helpers |
| `build.py` | `build_music_html`: add data attrs |
| `build.py` | `fetch_instapaper_starred`: extract `description` field |
| `build.py` | `build_article_html`: remove inner `<a>` wrapper; add data attrs |
| `build.py` | `main()`: pass `TMDB_API_KEY` env var to film build |
| `index.html` | Add modal HTML at bottom of `<body>` |
| `index.html` | Add modal JS inline script |
| `style.css` | Add modal CSS rules |
| `.github/workflows/build.yml` | Add `TMDB_API_KEY: ${{ secrets.TMDB_API_KEY }}` env var |

---

## New GitHub Secret

`TMDB_API_KEY` — free account at themoviedb.org. Add to repo settings → Secrets → Actions.

---

## What's Not in Scope

- No modal animation beyond a simple fade (matches existing boot overlay style)
- No swipe/gesture navigation between modal items
- No image lazy loading or blur-up placeholder
- TMDB failures are silent — film modals degrade to title/year/stars/Letterboxd link
- No modal for the "currently reading" status strip (only the recently-read panel rows)
