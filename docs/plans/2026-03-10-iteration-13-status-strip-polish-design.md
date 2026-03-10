# Iteration 13 — Status Strip Polish: Design

**Date:** 2026-03-10
**Status:** Approved

## Overview

Small CSS/template pass on the now-reading and now-playing status strips. Three changes: side-by-side layout on desktop, removal of the "by" connector word, and updated HTML/JS to use semantic spans for title vs author/artist contrast.

---

## Change 1 — Desktop side-by-side layout

Wrap both strips in a new `<div class="status-strips">` container in `index.html`. The `<!-- goodreads-now:start/end -->` marker and `#now-playing-strip` both move inside this wrapper.

**CSS:**
- Default (mobile): `display: flex; flex-direction: column; gap: var(--space-3)`
- `@media (min-width: 768px)`: `flex-direction: row; align-items: stretch` with `flex: 1` on each `.status-strip` inside the container

When now-playing is `hidden`, it doesn't participate in flex layout — the reading strip fills full width naturally.

---

## Change 2 — Remove "by" connector

Add a `.status-strip-name` CSS rule with `color: var(--text-secondary)` to style the author/artist name in muted grey, contrasted against the bright white italic title.

Both strips render: `<em>Title</em> <span class="status-strip-name">Name</span>` — no connector word needed.

---

## Change 3 — `build_now_reading_html()` update (`build.py`)

| Case | Old output | New output |
|------|-----------|------------|
| 1 book | `<em>Title</em> by Author` | `<em>Title</em> <span class="status-strip-name">Author</span>` |
| 2+ books | `<em>Title 1</em>, <em>Title 2</em>` | unchanged (titles only, no authors) |

---

## Change 4 — Now-playing JS update (`index.html`)

Currently: `text.textContent = d.track + ' by ' + d.artist`

New approach: clear `#now-playing-text`, then append two child nodes via DOM:
1. `<em>` with `textContent = d.track`
2. `<span class="status-strip-name">` with `textContent = d.artist`

Using `textContent` on each child safely handles special characters without `innerHTML`.

---

## Files changed

| File | Change |
|------|--------|
| `style.css` | Add `.status-strips` container rules + `.status-strip-name` colour rule; add `@media` desktop rule |
| `index.html` | Add `.status-strips` wrapper around both strips; update now-playing JS |
| `build.py` | Update `build_now_reading_html()` single-book branch |
