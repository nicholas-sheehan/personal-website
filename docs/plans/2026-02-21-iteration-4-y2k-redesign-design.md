# Iteration 4 — Y2K Visual Redesign Design

**Date:** 2026-02-21
**Status:** Approved

## Vision

A full aesthetic overhaul of nicsheehan.com. The site becomes a "public dashboard of my life" — a living, auto-updating readout of taste and activity across books, films, music, and articles. The visual language is Y2K / PS2 Memory Card: dark, structured, monospace, with colour-coded panels per content type.

This replaces the incremental approach of the original iterations 4, 5, and 6. Everything visual is redesigned as a coherent whole.

## Design Direction: PS2 Memory Card (selected)

Each content section is a panel/card styled like a PS2 save slot — dark background, coloured top border per section, all-caps mono section label, dense data rows. The overall page reads like a HUD.

**Note to frontend-designer:** You have latitude to push back on any of the below. If something doesn't work visually, or you see a better interpretation of the PS2/Y2K brief, flag it. The direction is the brief, not a pixel spec.

## Aesthetic Tokens

| Property | Value |
|----------|-------|
| Background | `#050a14` (blue-tinted black) |
| Panel background | `#0d1520` (slightly lifted) |
| Font | `JetBrains Mono` — single family, all weights, all text |
| Light mode | Removed entirely — dark only |

## Section Colour Coding

| Section | Colour | Hex |
|---------|--------|-----|
| Books | Green | `#22c55e` |
| Films | Amber | `#f59e0b` |
| Music | Purple | `#a855f7` |
| Articles | Blue | `#3b82f6` |

## Layout

### Profile / Header
Horizontal "system header" bar at top — avatar inline with name and tagline. Feels like a logged-in user bar. Nav links in mono below or alongside.

### Currently Reading (status strip)
Full-width strip above the content grid. Green accent. Mono prose: "NOW READING: *Zorba the Greek*". Hidden entirely when shelf is empty. Not a panel — more like a status bar.

### Content Grid
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

### Footer / Colophon
Mono, minimal. Fits the terminal aesthetic. Retains "Last built" timestamp.

## Content Counts (site.toml)
All four content sections standardised to **5 items** each:
- `sources.goodreads.read_limit = 5` (already 5)
- `sources.letterboxd.limit = 5` (currently 8, reduce to 5)
- `sources.lastfm.limit = 5` (currently 8, reduce to 5)
- `sources.instapaper.limit = 5` (already 5)

## Typography
Single monospace font throughout — `JetBrains Mono`. No sans-serif, no display font. All text: labels, headings, content, nav, footer.

## What This Replaces
The following roadmap items are superseded by this redesign and should not be implemented separately:
- Content-aware grid (old spec: `1fr 1fr` with articles full-width)
- Ratings-led film layout (will be handled in redesign)
- Articles with more presence (will be handled in redesign)
- Accent colour change (now per-section colour coding)
- Self-host fonts / reduce families (replaced by full mono)
- List item density tweaks (absorbed into redesign)

## What Carries Over (Iteration 5)
These features are not visual and ship separately after the redesign:
- Currently reading callout — build.py logic (`build_now_reading_html()`, new marker)
- Section headings linking to sources
- Footer countdown (build.py + minimal inline JS)
- Colophon copy: "Powered by" → "Built daily from"

## Roadmap Resequencing

| Old | New |
|-----|-----|
| Iteration 4 — Layout restructure | **Iteration 4 — Y2K Visual Redesign** (this) |
| Iteration 5 — Content presentation | **Iteration 5 — Content features** (non-visual items above) |
| Iteration 6 — Polish | Absorbed into iteration 4 |

---

## Alternative Layout Directions (for future reference)

These were considered and set aside in favour of the PS2 Memory Card direction. Saved here for potential future exploration.

### Option B — Y2K Web Portal
More late-90s web aesthetic — sections styled like application windows with title bars, gradient fills, chunky borders. Heavier, more decorative, closer to what you'd have seen on a fan site in 2001. More maximalist. Risk: harder to make look intentional rather than kitsch.

### Option C — Ambient / PS1 Boot
Very dark, almost no structure — content floats against a near-black background with glowing accents and subtle geometric texture (dot grids, faint scanlines). More atmospheric and mysterious, less structured. Risk: hard to read at high information density, and the dashboard quality gets lost.
