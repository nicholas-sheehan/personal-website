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

## Iteration 9 — Item detail modal + links out ✅ shipped 2026-02-28
Makes content interactive and connected to source services.

- [x] Click any panel item → in-page modal overlay (accent border, monospace, ESC to dismiss)
- [x] Modal shows richer data stored as `data-*` attributes at build time: book cover + description, Last.fm album + bio, article excerpt
- [x] "View on [Service] →" link inside each modal
- [x] TMDB integration for films — poster, director, synopsis via TMDB API (TMDB_API_KEY secret)

**Extras landed with this iteration:**
- Frontend-designer review: `[ X ]` close button, OS window chrome header, 400px max-width, cover image left-aligned 80px wide, backdrop-filter blur, modal link styled as panel-footer-link
- Fixed Last.fm bio suffix regex (`Read more on Last.fm` not `Read more about`)
- Consistent `html.escape(quote=True)` on all data attribute values

## Iteration 10 — Book modal enhancements ✅ shipped 2026-03-03
Small data quality improvements to the book panel modals. Plan: `docs/plans/2026-03-02-book-modal-enhancements.md`.

- [x] Higher-res cover images — use `book_large_image_url` (fallback to `book_image_url`)
- [x] Finished date — extract `user_read_at`, render "Finished Month Year" in modal meta
- [x] User review over synopsis — show own Goodreads review in modal if present, else synopsis

## Iteration 11 — Visual polish & modal improvements ✅ shipped 2026-03-05
Pure frontend — no new infrastructure. Quick wins that make the site feel more considered.

- [x] Heading distortion — replaced with full-page warm-up animation: brightness ease-out (0.6s) on `<main>` after boot completes
- [x] Modal close button — moved to top-right
- [x] Modal synopsis length — max-width increased to 560px, line-clamp removed
- [x] Modal meta hierarchy — source data (author/year/artist) in grey, personal data (stars/date/plays) in panel accent colour, two separate lines
- [x] Modal navigation — ← → buttons flanking index counter, keyboard arrow support, scoped to panel
- [x] Bottom panel alignment — added → Last.fm footer link to music panel

**Extras landed with this iteration:**
- Frontend designer review: reduced warm-up blur to 0 (brightness-only), improved arrow button padding/colour/disabled opacity

## Iteration 12 — Currently playing (live API) ✅ shipped 2026-03-10
First live data source — small serverless layer alongside the static site.

- [x] Cloudflare Worker proxying Last.fm `user.getRecentTracks` (`nowplaying` flag); `LASTFM_API_KEY` as Cloudflare secret
- [x] Static page `fetch()`es Worker on load; injects track if playing, otherwise section hidden
- [x] "Currently playing" strip with purple accent, matching currently-reading callout style
- [x] Animating CSS waveform icon (bars scaling up/down) to denote live data

**Extras landed with this iteration:**
- Added `worker/.gitignore` to exclude `.wrangler/` cache from repo (caught during implementation)
- Frontend designer review: `aria-live="polite"` on strip, animation speed 0.8s→0.5s, `min-width: 0` on `.status-strip-text`

## Iteration 13 — Status strip polish ✅ shipped 2026-03-10
Small CSS/template pass on the now-reading and now-playing strips.

- [x] Desktop: now-reading + now-playing strips side-by-side (flex row) on desktop, stacked on mobile — avoids two rows of chrome when both are visible
- [x] Remove "by" connector word from both strips — rely on colour contrast alone: title in `--text-primary`, author/artist name in `--text-secondary` via `.status-strip-name` span
- [x] Update `build_now_reading_html()` in `build.py` to output `<em>Title</em> <span class="status-strip-name">Author</span>`
- [x] Update now-playing JS IIFE to build separate spans for track and artist

**Extras landed with this iteration:**
- Added `min-width: 0` to `.status-strips .status-strip` desktop rule to prevent long titles overflowing flex container (caught in code quality review)

## Iteration 14 — Visual & Data Polish ✅ shipped 2026-03-11
Batch of small fixes from full design + technical review. No new infrastructure.

- [x] Typography: `.track-title` font-weight 500→400, `.article-title` 0.75rem→0.78rem, all remaining `font-weight: 500` → 400
- [x] CSS: modal `100vh`→`100dvh`, `panel-footer-link` `:focus-visible`, Google Fonts weight restriction (400/700 only), `.status-strip-title` class with link hover, `.modal-desc-label` class, panel flex column for footer alignment
- [x] HTML: Music panel → second position (Books→Music→Films→Articles), avatar dimensions 96→72 (via build.py), section subtitles standardised to "on [Service]"
- [x] Build: Goodreads UTM stripping, films watched date in modal, `article-source` span→div, now-reading strip clickable (linked title), `data-has-review` attr for books
- [x] JS: now-playing track not italic + clickable when URL available, film watched date in modal, modal link hidden when no URL, modal description labels (About/Review/Synopsis/Artist bio/Excerpt)
- [x] Worker: expose Last.fm track URL for clickable now-playing strip

**Extras landed with this iteration:**
- Removed Instapaper footer link from articles panel (would link to Instapaper login, not a public list)
- Book modal label switches between "About" (publisher synopsis) and "Review" (user's own Goodreads review) based on `data-has-review`

## Iteration 15 — Data Explorer Mode ⬜ planned 2026-02-22
Theatrical data experience. The biggest lift — requires a dedicated design session before implementation.

- [ ] Triggered by keyboard shortcut (`/` or `~`)
- [ ] Full-page takeover — aggregate stats + visualisations across all four data sources
- [ ] Navigation between views: reading history, listening patterns, watch log
- [ ] Detailed design to be brainstormed as its own session before implementation

---

## Dev environment improvements

**Priority — blocks proper release workflow:**
- [x] **Move DNS to Cloudflare nameservers** — done 2026-03-13. Added site in Cloudflare dashboard, updated nameservers at registrar, proxy enabled. ✅
- [x] **Migrate to Cloudflare Pages** — done 2026-03-13. `staging` now deploys to `staging.nicsheehan.pages.dev`; production at `www.nicsheehan.com`. Replaced GitHub Pages actions with `wrangler pages deploy` in CI. GitHub Pages disabled. ✅

**Other improvements:**
- [ ] **Restore `main` branch protection via GitHub Ruleset with deploy key bypass** — branch protection was removed 2026-03-02 because it blocked the build bot. Proper fix: create a Deploy Key for the bot and add it as a bypass actor in a Ruleset, then re-enable "Require a pull request before merging" on `main`. Without this, convention is the only guard and it will be violated (proven 2026-03-05).
- [ ] Switch git remote from HTTPS to SSH (`git remote set-url origin git@github.com:nicholas-sheehan/personal-website.git`) — requires SSH key set up with GitHub; prerequisite for the deploy key fix above
- [ ] Install `gh` CLI properly (Homebrew: `brew install gh`) so it doesn't need re-downloading each session
- [x] Squash-only merges — unticked "Allow merge commits" and "Allow rebase merging"; squash is now the only option, eliminating timestamp conflicts on `staging → main` ✅ 2026-03-03
- [ ] Process habit: commit any open docs/working-tree changes before starting worktree work — prevents `git checkout staging` failing mid-flow
- [ ] **Worker KV caching for now-playing** — cache Last.fm response in Cloudflare KV for ~15 seconds so rapid page loads don't hammer the API. One extra step in the Worker fetch handler. Bundle with a future iteration rather than shipping alone.
- [ ] **Pin `requirements.txt` versions** — `Pillow` and `tomli` are unpinned; a future Pillow major release could break OG image generation. Pin to `Pillow>=10,<12`.
- [ ] **API keys as request headers** — TMDB and Last.fm keys are passed as URL query params (visible in server logs). Switch to `Authorization` header pattern already used for Gravatar.
- [ ] **Wrangler deploy step in CI** — Worker code in `main` can drift from what's running on Cloudflare with no warning. Add a `wrangler deploy` step to the workflow so Worker deploys automatically on push.
- [ ] **HTML validation in CI** — no check that the build produces valid HTML. Add `html5validator` on `_site/` output to catch malformed markup before deploy.
- [ ] **OG image: skip regeneration if unchanged** — currently regenerated on every build even if Gravatar data hasn't changed. Add a hash/comparison guard to avoid the daily `og-image.png` git noise.
- [ ] **Boot sequence: skip on returning visits** — add a `sessionStorage` flag so the boot overlay is skipped for returning visitors; reduces artificial LCP delay from ~2.4–3.2s to near-zero on repeat loads.
- [ ] **CI deploy job: artifact handoff** — replace the second `git pull` in the `deploy` job with `actions/upload-artifact` / `actions/download-artifact` to pass `_site/` between jobs without a race-prone network pull.
- [ ] **CI deploy job: concurrency control** — add `concurrency:` key to cancel in-progress deploys when a new push arrives.

## Discussed and decided against
- Separate `twitter_title`/`twitter_description` in TOML — unnecessary, they always match `site.title`/`site.description`
- Moving JSON-LD fields to TOML — they correctly come from Gravatar (single source of truth)
