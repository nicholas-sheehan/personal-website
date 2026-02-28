# Site Improvement Roadmap

## Iteration 1 — Housekeeping & correctness ✅ shipped 2026-02-19
Pure fixes, no visual changes. Safe to batch and ship.

- [x] Remove all `twitter:*` meta tags (OG tags are sufficient, X falls back to them)
- [x] Update `build.py` docstring to reference `site.toml`
- [x] Fix JSON-LD duplicate `sameAs` URLs (normalize trailing slashes in `build_jsonld()`)
- [x] Inject `<html lang>` from `site.toml` `lang` field
- [x] Update `sitemap.xml` `<lastmod>` on each build
- [x] Timestamp format: "Last built 18 Feb 2026 at 10:00 UTC"

**Extras landed with this iteration:**
- Cleaned stale `twitter:` inline comments from `site.toml` (caught in code review)

## Iteration 2 — Build resilience & CI ✅ shipped 2026-02-19
Makes the build pipeline more robust before changing output.

- [x] Resilient builds — wrap feed fetches in try/except, keep existing content on failure
- [x] Cache pip install (Pillow) in CI for faster builds
- [x] Deploy only site files to Pages (assemble `_site/` dir in workflow)
- [x] Strip URL tracking params from Instapaper links

**Extras landed with this iteration:**
- Fixed `_strip_tracking_params("#")` edge case — non-HTTP fallback URLs now returned as-is (caught in final review)

## Iteration 3 — Accessibility & contrast ✅ shipped 2026-02-19
Fixes that land before the design overhaul so we start from a compliant baseline.

- [x] Fix light mode contrast — tertiary `#a8a29e` on `#fafafa` is ~2.9:1 (fails AA), shift to cool grays _(light mode removed in iteration 4)_
- [x] Add skip-to-content link for keyboard accessibility
- [ ] Avatar border — soften to `var(--border)` _(reverted — keeping accent blue)_

**Extras landed with this iteration:**
- Tokenised `.colophon .credits` dark mode base rule (was hardcoded `#525252`, now `var(--text-tertiary)`) — caught in final review

## Iteration 4 — Y2K Visual Redesign ✅ shipped 2026-02-21
Full aesthetic overhaul. Y2K / PS2 Memory Card direction — dark only, full mono (JetBrains Mono), colour-coded panels per content type, 2×2 content grid. Collapses old iterations 4, 5 (visual items), and 6.

- [x] Music data pipeline (Last.fm fetch, build_music_html, markers, CSS) — shipped 2026-02-21
- [x] Frontend-designer produces complete Y2K HTML/CSS prototype
- [x] Integrate new style.css and index.html structure with build system
- [x] Standardise content counts to 5 across all sections
- [x] Currently reading status strip — goodreads-now marker placeholder added (build.py logic in iteration 5)
- [x] Remove light mode

**Extras landed with this iteration:**
- Updated all 4 `build_*_html()` functions to output `.panel-row` div structure matching the prototype (caught by visual comparison post-ship)
- Removed dead `.panel-list` CSS block (80 lines) from `style.css`

## Iteration 5 — Content features ✅ shipped 2026-02-22

- [x] Currently reading callout — `build_now_reading_html()` + `goodreads-now` marker + placeholder fix
- [x] Section headings link to sources (+ mono subtitles) — Books→Goodreads, Films→Letterboxd, all four panels get `.section-source`
- [x] Footer countdown: pulsing dot (CSS, with prefers-reduced-motion) + "next in Xh Ym" inline JS, degrades gracefully
- [x] Colophon copy: "Powered by" → "Built daily from" _(pre-completed in iteration 4)_

**Extras landed with this iteration:**
- Fixed `panel-count` vertical alignment (`align-self: flex-start`) — needed once panel headers gained two-line `.panel-heading` structure
- Added `prefers-reduced-motion` override for `.pulse-dot` (caught in final code review)

## Iteration 6 — Polish & Nav ✅ shipped 2026-02-22
Concrete feedback pass — sharpens the baseline before building new features.

- [x] Title truncation on desktop — `text-overflow: ellipsis` on `.book-title`, `.film-title`, `.article-title`, `.track-title` at `min-width: 768px`; mobile unchanged
- [x] Nav cleanup — remove Goodreads + Letterboxd from top nav; add contextual "→ Goodreads" / "→ Letterboxd" links at bottom of relevant panels; keep email + LinkedIn
- [x] Book star ratings — extract `<user_rating>` from Goodreads RSS, render `★★★★★` in `#22c55e` (integer 1–5, clamped); recently-read only
- [x] Footer text visibility — bump from `var(--text-tertiary)` to `var(--text-secondary)`
- [x] Footer timestamp locale — convert UTC to user's local timezone via inline JS (`toLocaleString()` with `data-built` attribute)
- [x] Footer language — "built" → "Last build:"

## Iteration 7 — Favicon & OG image redesign ✅ shipped 2026-02-22
Visual identity refresh — bring favicon and OG image in line with the Y2K aesthetic.

- [x] Bundle JetBrains Mono TTF under `assets/` for Pillow use
- [x] New `python3 build.py favicons` command for one-time favicon generation
- [x] Favicon redesign — dark `#050a14` background, accent-blue "N" in JetBrains Mono Bold; `favicon.png` (48px), `favicon-192.png` (192px), `favicon.ico` (multi-res 16/32/48)
- [x] OG image redesign — Y2K palette (`#050a14`), top+left accent border, JetBrains Mono font, `nicsheehan.com` label bottom-right; avatar layout unchanged

## Iteration 8 — Boot sequence + Easter egg ✅ shipped 2026-02-28
Theatrical delight. Extends the existing boot overlay with personality.

- [x] Randomised boot sequence — pool of ~20 quirky messages, pick 4–6 per load, display sequentially with `[ OK ]` / `[DONE]` suffixes
- [x] Snake easter egg — triggered by typing `SNAKE` anywhere on page; fullscreen, existing palette; ESC or game-over dismisses

## Iteration 9 — Item detail modal + links out ⬜ planned 2026-02-22
Makes content interactive and connected to source services.

- [ ] Click any panel item → in-page modal overlay (accent border, monospace, ESC to dismiss)
- [ ] Modal shows richer data stored as `data-*` attributes at build time: book cover + description, Last.fm album + bio, article excerpt
- [ ] "View on [Service] →" link inside each modal
- [ ] TMDB integration for films — decision deferred to implementation (director, synopsis, poster vs. build-time Letterboxd data only)

## Iteration 10 — Currently playing (live API) ⬜ planned 2026-02-22
First live data source — small serverless layer alongside the static site.

- [ ] Cloudflare Worker proxying Last.fm `user.getRecentTracks` (`nowplaying` flag); `LASTFM_API_KEY` as Cloudflare secret
- [ ] Static page `fetch()`es Worker on load; injects track if playing, otherwise section hidden
- [ ] "Currently playing" strip with purple accent, matching currently-reading callout style
- [ ] Animating CSS waveform icon (bars scaling up/down) to denote live data

## Iteration 11 — Data Explorer Mode ⬜ planned 2026-02-22
Theatrical data experience. The biggest lift.

- [ ] Triggered by keyboard shortcut (`/` or `~`)
- [ ] Full-page takeover — aggregate stats + visualisations across all four data sources
- [ ] Navigation between views: reading history, listening patterns, watch log
- [ ] Detailed design to be brainstormed as its own session before implementation

---

## Discussed and decided against
- Separate `twitter_title`/`twitter_description` in TOML — unnecessary, they always match `site.title`/`site.description`
- Moving JSON-LD fields to TOML — they correctly come from Gravatar (single source of truth)
