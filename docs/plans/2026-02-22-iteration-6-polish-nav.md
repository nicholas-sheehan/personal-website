# Iteration 6 — Polish & Nav Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Apply concrete feedback to sharpen the baseline — title truncation, nav cleanup, book ratings, and footer improvements.

**Architecture:** CSS-only for truncation and colour changes; `build.py` changes for nav filtering and book ratings; static HTML edits in `index.html` for panel footer links and JS script extension.

**Tech Stack:** Python 3, CSS, vanilla JS (~50 bytes added to inline script)

---

### Task 1: CSS — Title truncation on desktop

**Files:**
- Modify: `style.css`

Titles that wrap across two lines cause the 2×2 panel grid to fall out of alignment on desktop. Add `text-overflow: ellipsis` to all four title types inside the existing `@media (min-width: 768px)` block.

**Step 1: Add truncation rules inside the 768px media query**

Open `style.css`. Find the `@media (min-width: 768px)` block (it contains `.content-grid { grid-template-columns: 1fr 1fr; }` and `.article-row-inner`). Add these rules inside that block:

```css
  /* Panel title truncation — keep grid rows aligned on desktop */
  .book-title,
  .film-title,
  .article-title,
  .track-title {
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }
```

**Step 2: Run build and visually verify**

```bash
python3 build.py
```

Open `index.html` in a browser. On a wide viewport, long titles should be truncated with `…`. On mobile (narrow viewport or DevTools mobile emulation) titles should still wrap normally.

**Step 3: Commit**

```bash
git add style.css
git commit -m "feat: truncate long panel titles on desktop with ellipsis"
```

---

### Task 2: CSS + HTML — Panel footer links

**Files:**
- Modify: `style.css`
- Modify: `index.html`

Remove Goodreads and Letterboxd from the top nav (that happens in Task 3 via build.py). Add static "→ Goodreads" and "→ Letterboxd" links at the bottom of their respective panels. These are hardcoded static HTML — the URLs don't change.

**Step 1: Add `.panel-footer` and `.panel-footer-link` CSS to `style.css`**

Add after the `.panel-body` rule block (look for `.panel-body { padding: 0; }`):

```css
/* Panel footer — contextual service link */
.panel-footer {
  padding: var(--space-2) var(--space-5);
  border-top: 1px solid var(--border);
  display: flex;
  justify-content: flex-end;
}

.panel-footer-link {
  font-family: var(--font-mono);
  font-size: 0.6rem;
  font-weight: 400;
  color: var(--text-tertiary);
  text-decoration: none;
  letter-spacing: 0.06em;
  transition: color 0.1s ease;
}

.panel-footer-link:hover {
  color: var(--text-secondary);
}
```

**Step 2: Add Goodreads footer link to Books panel in `index.html`**

Find this block in `index.html` (around line 1082):
```html
<!-- goodreads-read:end -->
              </div>
            </section>
```

Replace with:
```html
<!-- goodreads-read:end -->
              </div>
              <footer class="panel-footer">
                <a href="https://www.goodreads.com/user/show/175639385" class="panel-footer-link" target="_blank" rel="noopener noreferrer">→ Goodreads</a>
              </footer>
            </section>
```

**Step 3: Add Letterboxd footer link to Films panel in `index.html`**

Find this block (around line 1137):
```html
<!-- letterboxd:end -->
              </div>
            </section>
```

Replace with:
```html
<!-- letterboxd:end -->
              </div>
              <footer class="panel-footer">
                <a href="https://letterboxd.com/tonic2" class="panel-footer-link" target="_blank" rel="noopener noreferrer">→ Letterboxd</a>
              </footer>
            </section>
```

**Step 4: Run build and verify**

```bash
python3 build.py
```

Open `index.html`. Books panel should show "→ Goodreads" in the bottom-right. Films panel should show "→ Letterboxd". Both are small, mono, tertiary colour, right-aligned. Hover darkens the colour slightly.

**Step 5: Commit**

```bash
git add style.css index.html
git commit -m "feat: add contextual panel footer links for Books and Films"
```

---

### Task 3: build.py — Filter nav links + book star ratings

**Files:**
- Modify: `build.py`
- Modify: `style.css`

Two changes in one task — both involve `build.py` and the Goodreads data pipeline.

**Step 1: Add domain exclusion constant to `build.py`**

Find the `_TRACKING_PARAMS` frozenset near line 513. Add this constant directly above `build_gravatar_links_html()` (around line 407):

```python
_NAV_EXCLUDED_DOMAINS = frozenset({"goodreads.com", "letterboxd.com"})
```

**Step 2: Filter excluded domains in `build_gravatar_links_html()`**

Find `build_gravatar_links_html()` (around line 407). Change the loop to skip excluded domains:

```python
def build_gravatar_links_html(profile: dict, email: str = "") -> str:
    """Build nav link buttons from Gravatar links + optional email.
    Excludes Goodreads and Letterboxd — they have contextual panel footer links instead.
    """
    links = profile.get("links", [])
    lines = []
    for link in links:
        url = link.get("url", "")
        domain = urllib.parse.urlparse(url).hostname or ""
        domain = domain.removeprefix("www.")
        if domain in _NAV_EXCLUDED_DOMAINS:
            continue
        label = html.escape(link["label"])
        url_esc = html.escape(url)
        lines.append(
            f'                <a href="{url_esc}" class="system-nav-link" target="_blank" rel="noopener noreferrer">{label}</a>'
        )
    if email:
        lines.append(
            f'                <a href="mailto:{html.escape(email)}" class="system-nav-link">Email</a>'
        )
    return "\n".join(lines)
```

**Step 3: Update `fetch_goodreads()` to extract user_rating**

Find `fetch_goodreads()` (line 104). The Goodreads RSS includes a `<user_rating>` tag (integer 0–5; 0 = unrated). Update the function:

```python
def fetch_goodreads(rss_url: str, limit: int = 0) -> list[dict]:
    """Return a list of {title, author, rating} dicts from the RSS feed."""
    req = urllib.request.Request(rss_url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=15) as resp:
        tree = ET.parse(resp)

    books = []
    for item in tree.findall(".//item"):
        title_el = item.find("title")
        author_el = item.find("author_name")
        rating_el = item.find("user_rating")

        if title_el is None or title_el.text is None:
            continue

        title = title_el.text.strip()
        author = author_el.text.strip() if author_el is not None and author_el.text else "Unknown"
        rating_text = rating_el.text.strip() if rating_el is not None and rating_el.text else "0"
        rating = int(rating_text) if rating_text.isdigit() else 0
        books.append({"title": title, "author": author, "rating": rating})

        if limit and len(books) >= limit:
            break

    return books
```

**Step 4: Update `build_book_html()` to render star ratings**

Find `build_book_html()` (line 128). Add star rendering matching the `build_film_html()` pattern:

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
        if rating:
            aria = f' aria-label="Rated {rating} out of 5"'
            stars_html = f'\n                  <span class="row-meta book-stars"{aria}>{"★" * rating}</span>'
        else:
            stars_html = ""
        lines.append(
            f'                <div class="panel-row">\n'
            f'                  <span class="row-index">{idx}</span>\n'
            f'                  <div class="row-content">\n'
            f'                    <div class="book-title">{t}</div>\n'
            f'                    <div class="book-author">{a}</div>\n'
            f'                  </div>{stars_html}\n'
            f'                </div>'
        )
    return "\n".join(lines)
```

**Step 5: Add `.book-stars` CSS to `style.css`**

Find `.film-stars` in `style.css` (in the `/* --- FILMS rows --- */` section). Add `.book-stars` directly after `.film-stars`:

```css
/* Stars in green (books) */
.book-stars {
  font-style: normal;
  font-size: 0.7rem;
  color: var(--accent-books);
  letter-spacing: -0.02em;
  white-space: nowrap;
}
```

**Step 6: Run build and verify**

```bash
python3 build.py
```

Open `index.html`. Verify:
- Top nav shows only LinkedIn and Email (Goodreads and Letterboxd gone)
- Books panel rows show green stars `★★★★★` on the right for rated books; unrated have blank space
- Note: if `user_rating` is absent from the RSS, all books show no stars — that's fine (fail-safe, not crash)

**Step 7: Commit**

```bash
git add build.py style.css
git commit -m "feat: filter Goodreads/Letterboxd from nav, add green star ratings to books panel"
```

---

### Task 4: Footer improvements — visibility, language, locale timestamp

**Files:**
- Modify: `style.css`
- Modify: `build.py`
- Modify: `index.html` (inline JS script only)

Three footer changes: brighter text, "Last build:" language, and JS locale conversion of the UTC timestamp.

**Step 1: Bump footer text colours in `style.css`**

Find `.colophon-timestamp` (in the `/* FOOTER / COLOPHON */` section). Change `color: var(--text-tertiary)` to `var(--text-secondary)`:

```css
.colophon-timestamp {
  font-family: var(--font-mono);
  font-size: 0.65rem;
  font-weight: 400;
  color: var(--text-secondary);   /* was: var(--text-tertiary) */
  letter-spacing: 0.1em;
  text-transform: uppercase;
}
```

Find `.colophon-credits`. Change `color: var(--text-dim)` to `var(--text-tertiary)`:

```css
.colophon-credits {
  font-family: var(--font-mono);
  font-size: 0.65rem;
  font-weight: 400;
  color: var(--text-tertiary);   /* was: var(--text-dim) */
  letter-spacing: 0.04em;
}
```

**Step 2: Update `cmd_build()` timestamp HTML in `build.py`**

Find the `# ── Last built timestamp + countdown ──` section in `cmd_build()` (around line 877). Change the `updated_html` variable to:
- Use "Last build:" instead of "Last built"
- Wrap the UTC timestamp text in `<span class="colophon-buildtime" data-built="{iso}">` so JS can replace it

```python
    # ── Last build timestamp + countdown ──
    now = datetime.now(timezone.utc)
    next_build = _next_build_utc(now)
    next_iso = next_build.strftime("%Y-%m-%dT%H:%M:%SZ")
    built_iso = now.strftime("%Y-%m-%dT%H:%M:%SZ")
    updated_str = now.strftime("%-d %b %Y at %H:%M UTC")
    updated_html = (
        f'            <p class="colophon-timestamp">'
        f'<span class="pulse-dot" aria-hidden="true"></span>'
        f' Last build: <span class="colophon-buildtime" data-built="{built_iso}">{updated_str}</span>'
        f'<span class="next-update" data-next="{next_iso}"></span>'
        f'</p>'
    )
    src = inject(src, UPDATED_PATTERN, updated_html, "updated")
    print(f"  Timestamp: {updated_str} · next build: {next_iso}")
```

**Step 3: Extend the inline JS countdown script in `index.html`**

Find the inline `<script>` tag near the bottom of `index.html` (just before `<!-- analytics:start -->`). It currently reads:

```html
<script>(function(){var e=document.querySelector('.next-update');if(!e)return;function t(){var n=new Date(e.dataset.next),d=n-new Date();if(d<=0){e.textContent=' · updating soon';return;}var h=Math.floor(d/3600000),m=Math.floor((d%3600000)/60000);e.textContent=' · next in '+h+'h '+m+'m';}t();setInterval(t,60000);})();</script>
```

Replace with this extended version that also localises the build time:

```html
<script>(function(){var b=document.querySelector('.colophon-buildtime');if(b&&b.dataset.built){try{b.textContent=new Date(b.dataset.built).toLocaleString(undefined,{day:'numeric',month:'short',year:'numeric',hour:'2-digit',minute:'2-digit'});}catch(x){}}var e=document.querySelector('.next-update');if(!e)return;function t(){var n=new Date(e.dataset.next),d=n-new Date();if(d<=0){e.textContent=' \xb7 updating soon';return;}var h=Math.floor(d/3600000),m=Math.floor((d%3600000)/60000);e.textContent=' \xb7 next in '+h+'h '+m+'m';}t();setInterval(t,60000);})();</script>
```

Note: `\xb7` is the middle dot `·` — keeps the script safely ASCII.

**Step 4: Run build and verify**

```bash
python3 build.py
```

Open `index.html`. Verify:
- Footer text is visibly brighter — "Last build:" label and credits line should be clearly readable
- The timestamp reads something like "22 Feb 2026 at 10:30 pm" (locale-formatted, your local time)
- The "· next in Xh Ym" countdown still works
- Falls back gracefully if JS is disabled (shows raw UTC text from the build)

**Step 5: Commit**

```bash
git add style.css build.py index.html
git commit -m "feat: footer visibility, Last build language, UTC-to-local timestamp"
```

---

### Task 5: Final verification and push

**Step 1: Git pull before push**

```bash
git stash  # if any uncommitted changes
git pull --rebase origin main
git stash pop  # if stashed
```

If there's a rebase conflict on `<!-- updated:start/end -->`: keep OUR HTML structure, use the bot's (newer) timestamp text.

**Step 2: Verify full build from clean state**

```bash
python3 build.py
```

Check the output for any WARNING lines about missing markers. There should be none.

**Step 3: Visual checklist before push**

Open `index.html` in a browser and confirm all six changes:
- [ ] Long titles truncate with `…` on desktop; wrap normally on mobile
- [ ] Top nav: only LinkedIn and Email (no Goodreads, no Letterboxd)
- [ ] Books panel bottom-right: "→ Goodreads" link
- [ ] Films panel bottom-right: "→ Letterboxd" link
- [ ] Books panel: green stars on rated books (may show no stars if Goodreads RSS lacks `user_rating` — acceptable)
- [ ] Footer: brighter text, "Last build:" label, locale-formatted timestamp

**Step 4: Push**

```bash
git push origin main
```

**Step 5: Update roadmap**

Mark Iteration 6 as shipped in `.claude/roadmap.md`. Change `⬜ planned` to `✅ shipped YYYY-MM-DD`.

---

## Reference: Token values (do not hardcode elsewhere)

- Goodreads profile URL: `https://www.goodreads.com/user/show/175639385`
- Letterboxd profile URL: `https://letterboxd.com/tonic2`
- `--text-secondary`: `#7a8fa6`
- `--text-tertiary`: `#3d5166`
- `--text-dim`: `#2a3a4d`
- `--accent-books`: `#22c55e`
