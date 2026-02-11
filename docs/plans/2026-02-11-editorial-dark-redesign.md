# Editorial Dark Redesign

## Direction

Editorial dark mode with typographic hierarchy. A personal consumption dashboard that looks designed, not templated. Criterion Channel energy — confident, restrained, distinctive.

## Design Tokens

### Colors

| Role | Value | Notes |
|------|-------|-------|
| Background | `#0a0a0a` | Near-black, cold |
| Primary text | `#e5e5e5` | Not pure white |
| Secondary text | `#a3a3a3` | Bio, list items, metadata |
| Tertiary text | `#737373` | Footer, timestamps |
| Accent | `#3b82f6` | Clean blue — links, hovers, avatar ring |
| Accent hover | `#60a5fa` | Lighter blue for hover states |
| Borders | `#262626` | Subtle dividers |
| Surface | `#141414` | Hover backgrounds, cards |

### Typography

| Role | Font | Weight | Size |
|------|------|--------|------|
| Name (h1) | Space Grotesk | 700 | 3.5rem (desktop), 2.5rem (mobile) |
| Section headings (h2) | Space Grotesk | 600 | 1rem |
| Body / list items | Inter | 400 | 0.95rem |
| Metadata (years, sources, tagline) | JetBrains Mono | 400 | 0.8rem |
| Nav links | Inter | 500 | 0.85rem |

### Spacing

- Hero margin-bottom: 3rem
- Content grid gap: 2rem
- Section internal spacing: 0.75rem between items
- Page padding: 4rem 2rem (desktop), 2.5rem 1.25rem (mobile)

## Layout

### Desktop (>= 768px)

```
|  Name (large, left-aligned)          |
|  Tagline (monospace, secondary)      |
|  Bio (secondary text)                |
|                                      |
|  Books     |  Films      |  Reads   |
|  --------  |  ---------  |  ------- |
|  item      |  item ★★★★  |  item    |
|  item      |  item ★★★½  |  item    |
|            |  item ★★★   |  item    |
|                                      |
|  nav: LinkedIn  Goodreads  etc       |
|  Last updated: 2026-02-11           |
```

- Container max-width: 56rem (wider than current 34rem)
- Three-column CSS Grid for content sections
- Avatar: top-left of hero, accent-color ring border

### Mobile (< 768px)

- Single column, stacked sections
- Name still large but scaled down
- Grid collapses to stack

## Components

### Hero
- Name: Space Grotesk 700, 3.5rem desktop / 2.5rem mobile, letter-spacing -0.03em
- Avatar: circular, accent border ring (2px solid accent), positioned beside name on desktop
- Tagline: JetBrains Mono 400, 0.8rem, secondary color
- Bio: Inter 400, secondary color

### Content Sections
- h2: Space Grotesk 600, 1rem, uppercase, letter-spacing 0.05em, tertiary color — quiet labels
- List items: Inter 400, primary color for titles, secondary for metadata
- Star ratings: accent color, no glow — just the color is enough
- Source domains: JetBrains Mono, tertiary color
- Dividers: 1px solid borders color between items

### Nav
- Flat text links, no borders or pills
- Accent color on hover
- Arrow icon: translateX(2px) on hover, 0.1s transition
- Compact, inline, separated by middot or slash

### Footer
- "Last updated [date]" in JetBrains Mono, tertiary color
- Credits on same line or below, even more dimmed

## Interactions

- All transitions: 0.1s ease
- Link hover: color shift to accent
- List item hover: left border accent highlight (2px)
- Nav hover: accent color + arrow translateX
- Focus-visible: 2px accent outline, 2px offset

## Accessibility

- All text passes WCAG AA against #0a0a0a
- Primary #e5e5e5 on #0a0a0a = 16.5:1
- Secondary #a3a3a3 on #0a0a0a = 9.2:1
- Tertiary #737373 on #0a0a0a = 4.9:1 (passes AA)
- Accent #3b82f6 on #0a0a0a = 5.3:1 (passes AA)
- Print stylesheet: light background, dark text
- prefers-color-scheme: light gets a light variant

## What's NOT Changing

- Build system (build.py, comment markers, GitHub Actions)
- Data sources (Gravatar, Goodreads, Letterboxd, Instapaper)
- HTML structure (minor adjustments only — class additions, layout wrappers)
- No JavaScript

## Implementation Order

1. Fonts — add Space Grotesk + JetBrains Mono to Google Fonts link
2. CSS rewrite — new palette, layout grid, typography, components
3. HTML adjustments — add grid wrapper, update class names, add last-updated marker
4. build.py — add last-updated timestamp injection, update any HTML generation
5. Light mode — add prefers-color-scheme: light styles
6. Print styles — update for new design
7. Responsive — mobile breakpoints
