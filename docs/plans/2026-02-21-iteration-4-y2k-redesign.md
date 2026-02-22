# Iteration 4 — Y2K Visual Redesign

**Date:** 2026-02-21
**Status:** Shipped ✅

---

## Design

### Vision

A full aesthetic overhaul of nicsheehan.com. The site becomes a "public dashboard of my life" — a living, auto-updating readout of taste and activity across books, films, music, and articles. The visual language is Y2K / PS2 Memory Card: dark, structured, monospace, with colour-coded panels per content type.

This replaces the incremental approach of the original iterations 4, 5, and 6. Everything visual is redesigned as a coherent whole.

### Design Direction: PS2 Memory Card (selected)

Each content section is a panel/card styled like a PS2 save slot — dark background, coloured top border per section, all-caps mono section label, dense data rows. The overall page reads like a HUD.

**Note to frontend-designer:** You have latitude to push back on any of the below. If something doesn't work visually, or you see a better interpretation of the PS2/Y2K brief, flag it. The direction is the brief, not a pixel spec.

### Aesthetic Tokens

| Property | Value |
|----------|-------|
| Background | `#050a14` (blue-tinted black) |
| Panel background | `#0d1520` (slightly lifted) |
| Font | `JetBrains Mono` — single family, all weights, all text |
| Light mode | Removed entirely — dark only |

### Section Colour Coding

| Section | Colour | Hex |
|---------|--------|-----|
| Books | Green | `#22c55e` |
| Films | Amber | `#f59e0b` |
| Music | Purple | `#a855f7` |
| Articles | Blue | `#3b82f6` |

### Layout

**Profile / Header**
Horizontal "system header" bar at top — avatar inline with name and tagline. Feels like a logged-in user bar. Nav links in mono below or alongside.

**Currently Reading (status strip)**
Full-width strip above the content grid. Green accent. Mono prose: "NOW READING: *Zorba the Greek*". Hidden entirely when shelf is empty. Not a panel — more like a status bar.

**Content Grid**
2×2 grid on desktop (768px+), single column on mobile.

```
┌─────────────────┬─────────────────┐
│ BOOKS           │ FILMS           │
│ ─────────────── │ ─────────────── │
│ Recently read   │ Recently watched│
│ ...             │ ...             │
├─────────────────┼─────────────────┤
│ MUSIC           │ ARTICLES        │
│ ─────────────── │ ─────────────── │
│ Listening lately│ Reads I rec.    │
│ ...             │ ...             │
└─────────────────┴─────────────────┘
```

Each panel:
- 2px coloured top border (section colour)
- Small all-caps mono label: `BOOKS`, `FILMS`, `MUSIC`, `ARTICLES`
- 5 items, standardised across all sections (controlled via `site.toml`)
- Content rows in mono, dense, structured

**Footer / Colophon**
Mono, minimal. Fits the terminal aesthetic. Retains "Last built" timestamp.

### Content Counts (site.toml)
All four content sections standardised to **5 items** each:
- `sources.goodreads.read_limit = 5` (already 5)
- `sources.letterboxd.limit = 5` (currently 8, reduce to 5)
- `sources.lastfm.limit = 5` (currently 8, reduce to 5)
- `sources.instapaper.limit = 5` (already 5)

### Typography
Single monospace font throughout — `JetBrains Mono`. No sans-serif, no display font. All text: labels, headings, content, nav, footer.

### What This Replaces
The following roadmap items are superseded by this redesign and should not be implemented separately:
- Content-aware grid (old spec: `1fr 1fr` with articles full-width)
- Ratings-led film layout (will be handled in redesign)
- Articles with more presence (will be handled in redesign)
- Accent colour change (now per-section colour coding)
- Self-host fonts / reduce families (replaced by full mono)
- List item density tweaks (absorbed into redesign)

### What Carries Over (Iteration 5)
These features are not visual and ship separately after the redesign:
- Currently reading callout — build.py logic (`build_now_reading_html()`, new marker)
- Section headings linking to sources
- Footer countdown (build.py + minimal inline JS)
- Colophon copy: "Powered by" → "Built daily from"

### Roadmap Resequencing

| Old | New |
|-----|-----|
| Iteration 4 — Layout restructure | **Iteration 4 — Y2K Visual Redesign** (this) |
| Iteration 5 — Content presentation | **Iteration 5 — Content features** (non-visual items above) |
| Iteration 6 — Polish | Absorbed into iteration 4 |

### Alternative Layout Directions (considered and set aside)

These were considered in favour of the PS2 Memory Card direction. Saved here for potential future exploration.

**Option B — Y2K Web Portal**
More late-90s web aesthetic — sections styled like application windows with title bars, gradient fills, chunky borders. Heavier, more decorative, closer to what you'd have seen on a fan site in 2001. More maximalist. Risk: harder to make look intentional rather than kitsch.

**Option C — Ambient / PS1 Boot**
Very dark, almost no structure — content floats against a near-black background with glowing accents and subtle geometric texture (dot grids, faint scanlines). More atmospheric and mysterious, less structured. Risk: hard to read at high information density, and the dashboard quality gets lost.

---

## Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Replace the current minimal aesthetic with a full Y2K / PS2 Memory Card visual redesign — dark only, full monospace (JetBrains Mono), colour-coded content panels in a 2×2 grid.

**Architecture:** The frontend-designer agent produces a static HTML/CSS prototype as the design source of truth. That prototype is then split: its CSS replaces `style.css` (which gets inlined at build time), and its HTML structure is grafted onto `index.html` with all existing `<!-- tag:start/end -->` content markers preserved. The build system (`build.py`) is unchanged except for content limit adjustments in `site.toml`.

**Tech Stack:** HTML/CSS (no new dependencies), JetBrains Mono via Google Fonts, existing Python build system.

---

### Before Starting

Create an isolated worktree:
```bash
cd "/Users/nicholassheehan/Documents/Claude Files/Personal website"
git worktree add .worktrees/feature-y2k -b feature/y2k-redesign
```

All work happens in `.worktrees/feature-y2k`.

---

### Context: Current Structure

**Current HTML layout (index.html):**
```
<body>
  <a class="skip-to-content" href="#main-content">Skip to content</a>
  <main id="main-content">
    <div class="container">
      <header class="hero">
        <img class="avatar" ...>           <!-- gravatar-avatar:start/end -->
        <h1><!-- gravatar-name:start/end --></h1>
        <p class="tagline mono"><!-- gravatar-tagline:start/end --></p>
      </header>
      <section class="bio">
        <!-- gravatar-bio:start/end -->
      </section>
      <div class="content-grid">
        <div class="reading-column">           ← wrapper to be removed
          <section class="reading">
            <h2>Currently reading</h2>
            <ul><!-- goodreads:start/end --></ul>
          </section>
          <section class="reading">
            <h2>Recently read</h2>
            <ul><!-- goodreads-read:start/end --></ul>
          </section>
        </div>
        <section class="reading">
          <h2>Recently watched</h2>
          <ul><!-- letterboxd:start/end --></ul>
        </section>
        <section class="reading">
          <h2>Reads I recommend</h2>
          <ul><!-- instapaper:start/end --></ul>
        </section>
        <section class="reading">
          <h2>Listening to lately</h2>
          <ul><!-- music:start/end --></ul>
        </section>
      </div>
      <nav class="links"><!-- gravatar-links:start/end --></nav>
      <footer class="colophon">
        <!-- updated:start/end -->
        <p class="credits">...</p>
      </footer>
    </div>
  </main>
  <!-- jsonld:start/end -->
  <!-- analytics:start/end -->
</body>
```

**Current CSS summary (style.css):**
- Design tokens: `--bg: #0a0a0a`, `--accent: #3b82f6`, `--font-mono: "JetBrains Mono"`
- Fonts: Space Grotesk (heading), Inter (body), JetBrains Mono (mono)
- Grid: `1fr` mobile → `repeat(3, 1fr)` desktop
- Light mode: `@media (prefers-color-scheme: light)` block exists — **to be removed**
- CSS is inlined at build time between `<!-- style:start/end -->` markers in `<head>`

**Content markers that MUST be preserved:**
`meta`, `analytics`, `jsonld`, `style`, `gravatar-avatar`, `gravatar-name`, `gravatar-tagline`, `gravatar-bio`, `gravatar-links`, `goodreads`, `goodreads-read`, `letterboxd`, `instapaper`, `music`, `updated`

---

### Task 1: Frontend-designer produces Y2K prototype

**Files:**
- Create: `docs/design/y2k-prototype.html` (designer's output — full static prototype)

**Brief for the frontend-designer agent:**

```
Design and build a complete static HTML/CSS prototype for nicsheehan.com.

DIRECTION: Y2K / PS2 Memory Card aesthetic. Dark only. Think PS2 boot/loading
screen — structured panels, coloured accents, monospace everything. This is a
"public dashboard of my life" — books, films, music, and articles as data readouts.

YOU HAVE LATITUDE TO PUSH BACK. If something in the brief doesn't work visually,
flag it and propose an alternative. The direction is the brief, not a pixel spec.

AESTHETIC:
- Background: #050a14 (blue-black, slightly different from pure black)
- Panel background: slightly lifted from page (e.g. #0d1520)
- Font: JetBrains Mono exclusively — single family, all weights, all text
- No sans-serif, no display font anywhere
- Dark only — no light mode

SECTION COLOUR CODING (coloured top border per panel):
- Books:    #22c55e (green)
- Films:    #f59e0b (amber)
- Music:    #a855f7 (purple)
- Articles: #3b82f6 (blue)

LAYOUT:
- Profile area: horizontal "system header" — avatar inline with name + tagline.
  Feels like a logged-in user bar, not a traditional hero section.
- Currently reading: full-width status strip between profile and grid.
  "NOW READING: [title]" in mono with green accent. Hidden when empty.
- Content grid: 2×2 on desktop, single column on mobile.
  Top row: Books (left) | Films (right)
  Bottom row: Music (left) | Articles (right)
- Each panel: coloured top border, small all-caps mono label (BOOKS / FILMS /
  MUSIC / ARTICLES), 5 content rows, dense and structured
- Footer: mono, minimal, fits terminal aesthetic

CONTENT (hardcode realistic placeholder data):
- Books (recently read, 5 items): book title + author per row
- Films (recently watched, 5 items): film title + year + star rating per row
- Music (top tracks, 5 items): track name + artist + play count per row
- Articles (recommended reads, 5 items): article title + source domain per row
- Profile: name "Nicholas Sheehan", tagline "Web professional · Melbourne"
- Currently reading: "Zorba the Greek by Nikos Kazantzakis"
- Nav links: LinkedIn, GitHub, Email

TECHNICAL CONSTRAINTS:
- The CSS will be extracted and used as style.css (it gets inlined into the HTML
  at build time — no separate stylesheet link needed in the final output, but
  include it in the prototype for preview purposes)
- JetBrains Mono must be loaded via Google Fonts <link> in the <head>
- The HTML will be adapted to include content injection markers — design the
  structure so each content area is a clearly bounded list or element
- Accessibility: skip-to-content link, semantic HTML, aria labels on sections
- Keep the skip-to-content link at the top of <body>

OUTPUT: Complete self-contained HTML file with embedded CSS (also in a <style>
tag for the prototype). Save to docs/design/y2k-prototype.html.
```

**Step 1: Create docs/design/ directory and dispatch frontend-designer**

```bash
mkdir -p docs/design
```

Then use the Task tool with subagent_type=frontend-designer, passing the full brief above. The designer will produce the prototype and save it to `docs/design/y2k-prototype.html`.

**Step 2: Review the prototype**

Open it in a browser:
```bash
open docs/design/y2k-prototype.html
```

Check:
- Does the overall aesthetic match the Y2K/PS2 brief?
- Are all four panels present with correct colour coding?
- Does the profile area read as a system header?
- Is the currently-reading strip distinct from the grid?
- Is the typography fully monospace?
- Does it look intentional and polished?

If the designer pushed back on any brief items, evaluate their suggestions and decide which to adopt before proceeding.

**Step 3: Commit the prototype**

```bash
git add docs/design/y2k-prototype.html
git commit -m "Add Y2K prototype from frontend-designer"
```

---

### Task 2: Extract CSS into style.css

**Files:**
- Modify: `style.css` (replace contents entirely)

**Step 1: Extract CSS from the prototype**

From `docs/design/y2k-prototype.html`, extract everything between `<style>` and `</style>` tags. This becomes the new `style.css`.

**Step 2: Verify the CSS includes all required elements**

Check that the extracted CSS covers:
- [ ] `:root` design tokens (new Y2K palette)
- [ ] Reset / base styles
- [ ] `.skip-to-content` (accessibility — must be preserved)
- [ ] Layout: `main`, `.container`
- [ ] Profile/hero area
- [ ] Currently-reading status strip
- [ ] `.content-grid` as 2×2 grid on desktop
- [ ] Panel styles (coloured borders, labels)
- [ ] Per-section content row styles
- [ ] Nav links
- [ ] Footer/colophon
- [ ] Responsive breakpoints (mobile single-column)
- [ ] Print styles (keep basic)
- [ ] **No light mode** `@media (prefers-color-scheme: light)` block

**Step 3: Write to style.css**

Replace `style.css` entirely with the extracted CSS. Add a comment header:

```css
/* ──────────────────────────────────────────────
   nicsheehan.com
   Y2K / PS2 Memory Card. Full mono.
   ────────────────────────────────────────────── */
```

**Step 4: Verify style.css is valid**

```bash
python3 -c "
css = open('style.css').read()
print('Lines:', len(css.splitlines()))
print('Has :root:', ':root' in css)
print('Has light mode (should be False):', 'prefers-color-scheme: light' in css)
print('Has skip-to-content:', 'skip-to-content' in css)
print('Has content-grid:', 'content-grid' in css)
"
```

Expected: light mode is False, all others True.

**Step 5: Commit**

```bash
git add style.css
git commit -m "Replace style.css with Y2K design"
```

---

### Task 3: Reconstruct index.html with Y2K structure

**Files:**
- Modify: `index.html`

This is the most complex task. The goal is to take the HTML *structure* from the designer's prototype and graft in all existing content injection markers.

**Step 1: Update the `<head>` font loading**

In `index.html`, find the existing font loading `<link>` tags in `<head>` (Space Grotesk, Inter, JetBrains Mono). Replace with JetBrains Mono only:

```html
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:ital,wght@0,400;0,500;0,700;1,400&display=swap" rel="stylesheet">
```

**Step 2: Update the profile/header area**

Replace the current `.hero` section with the new system header structure from the prototype. Maintain these markers exactly:
- `<!-- gravatar-avatar:start/end -->` — wraps the `<img>` tag
- `<!-- gravatar-name:start/end -->` — wraps the name text
- `<!-- gravatar-tagline:start/end -->` — wraps the tagline text
- `<!-- gravatar-bio:start/end -->` — wraps the bio paragraph

**Step 3: Add the currently-reading status strip**

Add the status strip element between the profile area and the content grid. This element will be wired up in Iteration 5 (when `build_now_reading_html()` is built). For now it holds placeholder text:

```html
<!-- goodreads-now:start -->
<!-- goodreads-now:end -->
```

(The marker is reserved for future use — build.py doesn't inject into it yet. The strip's show/hide behaviour will be handled in Iteration 5.)

**Step 4: Replace the content grid**

Replace the current `.content-grid` div (including the `.reading-column` wrapper) with the new 2×2 panel structure from the prototype.

Each panel must contain its existing content markers:

- **BOOKS panel:** `<!-- goodreads-read:start/end -->` inside the panel's list
  - Note: "Currently reading" (`<!-- goodreads:start/end -->`) moves to the status strip in Iteration 5. For now, remove the currently-reading section from the grid entirely — it will be reintroduced as the status strip.
- **FILMS panel:** `<!-- letterboxd:start/end -->`
- **MUSIC panel:** `<!-- music:start/end -->`
- **ARTICLES panel:** `<!-- instapaper:start/end -->`

Example panel structure (adapt to match designer's exact HTML):
```html
<section class="panel panel-books" aria-labelledby="books-heading">
  <h2 id="books-heading" class="panel-label">Books</h2>
  <ul class="panel-list">
<!-- goodreads-read:start -->
    <li>placeholder</li>
<!-- goodreads-read:end -->
  </ul>
</section>
```

**Step 5: Update nav links**

Ensure `<!-- gravatar-links:start/end -->` is inside the nav element from the new design.

**Step 6: Verify all markers survive**

```bash
python3 -c "
import build
with open('index.html') as f:
    src = f.read()

patterns = {
    'meta': build.META_PATTERN,
    'analytics': build.ANALYTICS_PATTERN,
    'jsonld': build.JSONLD_PATTERN,
    'style': build.STYLE_PATTERN,
    'gravatar-avatar': build.GRAVATAR_AVATAR_PATTERN,
    'gravatar-name': build.GRAVATAR_NAME_PATTERN,
    'gravatar-tagline': build.GRAVATAR_TAGLINE_PATTERN,
    'gravatar-bio': build.GRAVATAR_BIO_PATTERN,
    'gravatar-links': build.GRAVATAR_LINKS_PATTERN,
    'goodreads': build.GOODREADS_PATTERN,
    'goodreads-read': build.GOODREADS_READ_PATTERN,
    'letterboxd': build.LETTERBOXD_PATTERN,
    'instapaper': build.INSTAPAPER_PATTERN,
    'music': build.MUSIC_PATTERN,
    'updated': build.UPDATED_PATTERN,
}

all_ok = True
for name, pattern in patterns.items():
    found = pattern.search(src) is not None
    status = '✓' if found else '✗ MISSING'
    print(f'  {status} {name}')
    if not found:
        all_ok = False

print()
print('All markers found:', all_ok)
"
```

Expected: all markers show ✓.

**Step 7: Commit**

```bash
git add index.html
git commit -m "Reconstruct index.html with Y2K panel structure"
```

---

### Task 4: Standardise content limits in site.toml

**Files:**
- Modify: `site.toml`

**Step 1: Update limits**

Change:
```toml
[sources.letterboxd]
limit = 8    # → change to 5

[sources.lastfm]
limit = 8    # → change to 5
```

Goodreads read_limit and Instapaper limit are already 5 — leave them.

**Step 2: Verify**

```bash
python3 -c "
try:
    import tomllib
except ModuleNotFoundError:
    import tomli as tomllib
with open('site.toml', 'rb') as f:
    c = tomllib.load(f)
print('letterboxd limit:', c['sources']['letterboxd']['limit'])
print('lastfm limit:', c['sources']['lastfm']['limit'])
print('instapaper limit:', c['sources']['instapaper']['limit'])
print('goodreads read_limit:', c['sources']['goodreads']['read_limit'])
"
```

Expected: all four print `5`.

**Step 3: Commit**

```bash
git add site.toml
git commit -m "Standardise all content section limits to 5"
```

---

### Task 5: Run full build and verify

**Step 1: Run the build with all credentials**

```bash
GRAVATAR_API_KEY="..." \
INSTAPAPER_CONSUMER_KEY="..." \
INSTAPAPER_CONSUMER_SECRET="..." \
INSTAPAPER_OAUTH_TOKEN="..." \
INSTAPAPER_OAUTH_TOKEN_SECRET="..." \
LASTFM_API_KEY="..." \
python3 build.py
```

Expected: build completes with no WARNING lines about missing markers.

**Step 2: Open in browser**

```bash
open index.html
```

Check:
- [ ] Y2K aesthetic renders correctly
- [ ] All four panels show real data (5 items each)
- [ ] Profile area shows real name, tagline, avatar
- [ ] Bio renders
- [ ] Nav links render
- [ ] Footer shows "Last built" timestamp
- [ ] No broken layout or missing styles

**Step 3: Commit if clean**

```bash
git add index.html og-image.png sitemap.xml
git commit -m "Full build verification — Y2K redesign live"
```

---

### Task 6: Update documentation

**Files:**
- Modify: `README.md`
- Modify: `CLAUDE.md` (local only, not committed)
- Modify: `docs/roadmap.md`

**Step 1: Update README.md**

In the `## How it works` section, update the description to reflect the new aesthetic:

Change: `"A static site that pulls all its content from external services, rebuilt daily by GitHub Actions."`

To: `"A static site that pulls all its content from external services and presents it as a Y2K-inspired personal dashboard, rebuilt daily by GitHub Actions."`

Also remove any reference to light mode if present.

**Step 2: Update CLAUDE.md**

Add a note under Key decisions:
```
- Design aesthetic: Y2K / PS2 Memory Card — dark only, full monospace (JetBrains Mono), colour-coded panels
- Light mode removed in iteration 4
```

**Step 3: Update roadmap**

Mark iteration 4 items as complete.

**Step 4: Commit README**

```bash
git add README.md
git commit -m "Update README for Y2K redesign"
```

---

### Final: push

```bash
git restore index.html og-image.png sitemap.xml
git pull --rebase origin main
git push origin main
```

Then clean up:
```bash
git worktree remove .worktrees/feature-y2k
git branch -d feature/y2k-redesign
```
