# Iteration 7 — Favicon & OG Image Redesign

**Date:** 2026-02-22
**Status:** Approved

## Goal

Bring the favicon and OG image in line with the Y2K aesthetic established in iteration 4. Both currently use the old palette and non-monospace fonts.

---

## Font Strategy

Bundle JetBrains Mono TTF files in the repo under `assets/`:
- `assets/JetBrainsMono-Regular.ttf`
- `assets/JetBrainsMono-Bold.ttf`

Used by both `generate_og_image()` and `cmd_favicons()`. Falls back to DejaVu Mono if the asset files are missing. No network dependency at build time for font loading.

---

## OG Image

**Function:** `generate_og_image()` in `build.py` — updated in place.

**Dimensions:** 1200×630 (unchanged).

**Layout:** Same composition as current — avatar left, name + tagline right.

**Y2K treatment:**
- Background: `#050a14` (fix from old `#0a0a0a`)
- 2px top border + 4px left border in `#3b82f6` (blue panel accent)
- Avatar: circular crop + blue ring, same size and position (unchanged)
- Name: JetBrains Mono Bold, ~54px, `#e2e8f0`
- Tagline: JetBrains Mono Regular, ~24px, `#64748b`
- `nicsheehan.com` label: JetBrains Mono Regular, small, `#3b82f6`, bottom-right

**Files changed:** `build.py` (updated function), `og-image.png` (regenerated on every build as now).

---

## Favicons

**Command:** `python3 build.py favicons` — new `cmd_favicons()` function.

Not run on every build. Favicons are static assets — run once, commit the result. Re-run only if the design changes.

**Design:** `#050a14` background, `#3b82f6` "N" centred, JetBrains Mono Bold.

**Outputs:**
- `favicon.png` — 48×48
- `favicon-192.png` — 192×192
- `favicon.ico` — multi-res pack (16×16 + 32×32 + 48×48)

**Files changed:** `build.py` (new command), `favicon.png`, `favicon-192.png`, `favicon.ico`.

---

## Files Summary

| File | Change |
|------|--------|
| `assets/JetBrainsMono-Regular.ttf` | New — bundled font |
| `assets/JetBrainsMono-Bold.ttf` | New — bundled font |
| `build.py` | Update `generate_og_image()`, add `cmd_favicons()` |
| `favicon.png` | Replaced — Y2K design |
| `favicon-192.png` | Replaced — Y2K design |
| `favicon.ico` | Replaced — Y2K design |
| `og-image.png` | Regenerated on every build (CI artifact) |
