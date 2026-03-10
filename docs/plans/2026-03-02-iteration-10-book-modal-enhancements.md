# Book Modal Enhancements Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Improve book modal data by using higher-res cover images, adding a "Finished Month Year" date, and showing the user's own Goodreads review as the description when available.

**Architecture:** All changes are build-time only — `fetch_goodreads()` extracts new fields, `build_book_html()` emits new `data-*` attrs, and the static modal JS in `index.html` renders the finished date. No new markers, no CSS changes.

**Tech Stack:** Python 3.12, standard library (`email.utils`, `datetime`), inline JS (already present in `index.html`).

---

### Task 1: Extract new fields in `fetch_goodreads()`

**Files:**
- Modify: `build.py` — imports block (~line 53) and `fetch_goodreads()` (~line 118)

**Step 1: Add `email.utils` import**

In the imports block, add after `import email` or alongside other stdlib imports (alphabetical order — after `from datetime import ...`):

```python
from email.utils import parsedate
```

**Step 2: Extract `book_large_image_url`, `user_read_at`, `user_review` inside the `for item` loop**

Replace the existing field extraction block (lines ~128–144) with the expanded version:

```python
        title_el      = item.find("title")
        author_el     = item.find("author_name")
        rating_el     = item.find("user_rating")
        cover_el      = item.find("book_image_url")
        large_cover_el = item.find("book_large_image_url")
        desc_el       = item.find("book_description")
        review_el     = item.find("user_review")
        read_at_el    = item.find("user_read_at")
        link_el       = item.find("link")

        if title_el is None or title_el.text is None:
            continue

        title  = title_el.text.strip()
        author = author_el.text.strip() if author_el is not None and author_el.text else "Unknown"
        rating_text = rating_el.text.strip() if rating_el is not None and rating_el.text else "0"
        rating = min(int(rating_text), 5) if rating_text.isdigit() else 0
        cover       = cover_el.text.strip() if cover_el is not None and cover_el.text else ""
        large_cover = large_cover_el.text.strip() if large_cover_el is not None and large_cover_el.text else ""

        # Description: user review takes priority over synopsis
        review_raw = _strip_html(review_el.text.strip()) if review_el is not None and review_el.text else ""
        if len(review_raw) > 400:
            review_raw = review_raw[:397] + "…"
        synopsis_raw = _strip_html(desc_el.text.strip()) if desc_el is not None and desc_el.text else ""
        if len(synopsis_raw) > 400:
            synopsis_raw = synopsis_raw[:397] + "…"
        description = review_raw if review_raw else synopsis_raw

        # Finished date (read shelf only — currently-reading items have empty user_read_at)
        finished = ""
        if read_at_el is not None and read_at_el.text:
            parsed = parsedate(read_at_el.text.strip())
            if parsed:
                try:
                    finished = datetime(parsed[0], parsed[1], parsed[2]).strftime("Finished %B %Y")
                except Exception:
                    pass

        url = link_el.text.strip() if link_el is not None and link_el.text else ""
```

**Step 3: Add new fields to the returned dict**

Replace:
```python
        books.append({
            "title": title, "author": author, "rating": rating,
            "cover": cover, "description": description, "url": url,
        })
```

With:
```python
        books.append({
            "title": title, "author": author, "rating": rating,
            "cover": cover, "large_cover": large_cover,
            "description": description, "finished": finished, "url": url,
        })
```

**Step 4: Verify build runs without error**

```bash
python3 build.py
```

Expected: build completes, no exceptions. Check terminal output shows `Found 1 book(s) on currently-reading shelf.` and `Found 5 book(s) on read shelf.` as before.

**Step 5: Commit**

```bash
git add build.py
git commit -m "feat: extract large cover, finished date, and review from Goodreads RSS"
```

---

### Task 2: Emit new `data-*` attrs in `build_book_html()`

**Files:**
- Modify: `build.py` — `build_book_html()` (~line 157)

**Step 1: Update `data-cover` to use large image, add `data-finished`**

Find the data attrs block inside `build_book_html()`:
```python
        if book.get("cover"):
            data += f' data-cover="{html.escape(book["cover"], quote=True)}"'
```

Replace with:
```python
        cover_src = book.get("large_cover") or book.get("cover", "")
        if cover_src:
            data += f' data-cover="{html.escape(cover_src, quote=True)}"'
        if book.get("finished"):
            data += f' data-finished="{html.escape(book["finished"], quote=True)}"'
```

Note: `data-description` already uses `book["description"]` — no change needed, since Task 1 now puts review-over-synopsis into that field.

**Step 2: Verify build and inspect output**

```bash
python3 build.py
```

Then open `index.html` and search for `data-finished` — read shelf items that have a read date should show e.g. `data-finished="Finished January 2024"`. Currently-reading items should have no `data-finished` attr.

Also check `data-cover` values look like larger image URLs (Goodreads large images are typically `...SY475_...` or similar vs small `...SY75_...`).

**Step 3: Commit**

```bash
git add build.py
git commit -m "feat: use large cover image and emit data-finished attr in book HTML"
```

---

### Task 3: Render finished date in modal JS

**Files:**
- Modify: `index.html` — modal JS book block (~line 1554)

**Step 1: Add `row.dataset.finished` to book meta parts**

Find:
```javascript
            if (type === 'book') {
              var bookParts = [row.dataset.author, row.dataset.stars].filter(Boolean);
              meta = bookParts.join(' · ');
```

Replace with:
```javascript
            if (type === 'book') {
              var bookParts = [row.dataset.author, row.dataset.stars, row.dataset.finished].filter(Boolean);
              meta = bookParts.join(' · ');
```

This renders as e.g. `Albert Camus · ★★★ · Finished January 2024` in the modal meta line. `.filter(Boolean)` means items without a date (currently reading) are unaffected.

**Step 2: Build and manually test in browser**

```bash
python3 build.py
open index.html
```

Click a book on the read shelf — modal meta should show `Author · Stars · Finished Month Year`.
Click the currently-reading book — modal meta should show `Author` only (no stars if unrated, no finished date).

**Step 3: Commit**

```bash
git add index.html
git commit -m "feat: show finished date in book modal"
```

---

### Final check

Run the full build one more time and confirm:
- No build errors
- `index.html` has `data-finished` on read shelf items
- Browser: book modals show correct data, cover images look higher res
- Currently-reading modal is unaffected
