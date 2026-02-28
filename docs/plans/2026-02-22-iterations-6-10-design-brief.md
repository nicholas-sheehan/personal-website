# Iterations 6–10 Design

_Brainstormed 2026-02-22. All five iterations approved._

---

## Iteration 6 — Polish & Nav

### Title truncation (desktop only)
- Apply `white-space: nowrap; overflow: hidden; text-overflow: ellipsis` to `.book-title`, `.film-title`, `.article-title`, `.track-title` at `min-width: 768px`
- Mobile unchanged — text continues to wrap naturally
- Keeps 2×2 grid panels in perfect horizontal alignment on desktop

### Nav cleanup
- Remove Goodreads and Letterboxd links from top nav (`<!-- nav:start/end -->`)
- Add a small "→ Goodreads" link at the bottom of the Books panel footer
- Add a small "→ Letterboxd" link at the bottom of the Films panel footer
- Email and LinkedIn remain in top nav

### Book star ratings
- Extract `<user_rating>` from Goodreads RSS in `build_books_html()`
- Render `★★★★☆` in `#22c55e` (book green) using the same `.film-rating` fixed-width column pattern
- Applies only to recently-read books (currently reading has no rating yet)
- Unrated entries get blank space to preserve alignment

### Footer improvements
- Bump text colour one step lighter: `var(--text-tertiary)` → `var(--text-secondary)`
- Convert UTC build timestamp to user's local timezone using inline JS on page load (`new Date(isoString).toLocaleTimeString()`)
- Language change: "built" → "Last build:" (short, technical, noun form, terminal aesthetic)

---

## Iteration 7 — Boot sequence + Easter egg

### Boot sequence
- Extend the existing CSS-only boot overlay with a small JS block
- Pool of ~20 quirky messages; pick 4–6 at random each page load
- Messages display sequentially with ~300ms gaps, each with a terminal status suffix (`[ OK ]`, `[DONE]`, `....`)
- Example messages: `LOADING STARS`, `MERGING BITSTREAMS`, `QUEUING AT DATABANK`, `CALIBRATING DISPLAY MATRIX`, `HANDSHAKING WITH DATABANK`
- Pool large enough that runs feel unique; overlay fades as it does now after sequence completes

### Easter egg — Snake
- Trigger: typing the word `SNAKE` anywhere on the page (global keystroke listener, silent buffer)
- Only discoverable by someone actively poking around
- Snake renders fullscreen over the site using the existing palette — green snake on `#050a14`, accent colours
- ESC or game-over dismisses it and returns to the site

---

## Iteration 8 — Item detail modal + links out

### In-page detail modal
- Clicking any panel item opens a modal overlay (dark, monospace, accent border matching panel colour)
- ESC or clicking outside dismisses it
- "View on [Service] →" link at bottom of modal
- Richer data fetched at build time, stored as `data-*` attributes on each panel item

### Data per panel
- **Films** — TMDB API integration decision deferred to implementation time; at minimum shows title, year, rating, Letterboxd link. TMDB would add director, synopsis, poster.
- **Books** — Goodreads RSS provides description/review text and cover image URL. No additional APIs needed.
- **Music** — Last.fm API provides album name, play count, artist bio. No additional APIs needed.
- **Articles** — Instapaper excerpt if available; otherwise domain + link is sufficient.

### Architecture note
- First meaningful JS addition beyond countdown and Snake (~1KB modal system, no dependencies)
- Consistent with terminal aesthetic

---

## Iteration 9 — Currently playing (live API)

### Architecture
- GitHub Pages is static-only; live data requires a serverless proxy
- Cloudflare Worker (free tier, edge-deployed, no cold starts): proxies `user.getRecentTracks` from Last.fm and returns the current `nowplaying` track as JSON
- `LASTFM_API_KEY` stored as a Cloudflare secret — never exposed to the browser
- Static page makes a single `fetch()` to the Worker on load; injects track if playing, otherwise section stays hidden

### UI
- Displayed as a strip matching the currently-reading callout pattern
- "Currently playing _Track_ by Artist" with purple music accent (`#a855f7`)
- Animating waveform icon (CSS — a few bars scaling up and down) sits next to the text to denote live data
- Consistent with the pulse dot aesthetic in the footer

---

## Iteration 10 — Data Explorer Mode

### Concept
- Theatrical, Jurassic Park-style interactive data experience ("this is a UNIX system!")
- Triggered by a keyboard shortcut (e.g. `/` or `~`) — discoverable but not obvious
- Full-page takeover in the existing palette

### Content
- Aggregate stats and visualisations across all four data sources
- Navigation between views: reading history, listening patterns, watch log, reading list
- The "exploring" and "surfing" feeling of 80s/90s computing aesthetics

### Notes
- The largest lift of all iterations — heavy JS
- Design direction (Alien terminal, Fallout PipBoy) remains a long-range horizon item that would naturally inform the aesthetic of this mode
- Detailed design to be brainstormed as its own session before implementation

---

## Discussed and decided against (iterations 6–10)
- Separate design overhaul for Alien/PipBoy direction — long-range horizon item, not actively planned
- TMDB API for films — deferred to iteration 8 implementation, needs more thought
