# Design: Book Modal Enhancements

**Date:** 2026-03-02
**Scope:** Build-time changes to `fetch_goodreads()` and `build_book_html()` only. No new markers, no CSS changes.

## What we're changing

Three improvements to how book data is extracted and displayed in the item detail modal:

### 1. Cover image quality
Use `book_large_image_url` as the primary cover image instead of `book_image_url`. Fall back to `book_image_url` if the large URL is empty.

### 2. Finished date (read shelf only)
Extract `user_read_at` from the RSS, parse it into "Finished [Month Year]" format, and pass it as a `data-finished` attribute on the `.panel-row`. The modal JS renders it as a line in the modal. Only shown when the value is non-empty (currently-reading items won't have it).

### 3. User review over synopsis
Extract `user_review` from the RSS, strip HTML via `_strip_html()`. If non-empty, pass as `data-description` instead of `book_description`. If empty, fall back to `book_description` as before. No new attribute needed — same `data-description` slot, better content when available.

## Data flow

```
fetch_goodreads()
  ├── extract book_large_image_url (fallback: book_image_url)
  ├── extract user_read_at → parse → "Finished Month Year" string
  └── extract user_review → strip HTML → use as description if non-empty

build_book_html()
  ├── data-cover = large image URL
  ├── data-finished = "Finished Month Year" (omit attr if empty)
  └── data-description = review if present, else synopsis
```

## Modal JS
The existing modal JS already renders `data-finished` if we add it — need to verify and add a render line if not already present. No structural changes to the modal HTML.

## Constraints
- Read-only change to existing `data-description` slot — no new modal fields needed for review
- `user_read_at` format in RSS is RFC 2822 (e.g. `Mon, 15 Jan 2024 00:00:00 -0800`) — parse with `email.utils.parsedate()` or `datetime.strptime`
- All values escaped via `html.escape(quote=True)` before injection into attributes
