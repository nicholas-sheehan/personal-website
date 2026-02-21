# Music Section — Last.fm Design

**Date:** 2026-02-21
**Status:** Approved

## Goal

Add music as a fourth media dimension to the site — alongside books, films, and articles. Shows the user's top tracks of the current month, pulled automatically from Last.fm at build time.

## Data Source

- **Service:** Last.fm API (`user.getTopTracks`)
- **Endpoint:** `https://ws.audioscrobbler.com/2.0/?method=user.getTopTracks&user={username}&period=1month&limit=8&api_key={key}&format=json`
- **Auth:** API key only (read-only public data) — `LASTFM_API_KEY` as a new GitHub secret
- **Config:** Last.fm username + limit go in `site.toml` under `[sources.lastfm]` (public config, same pattern as Letterboxd username)
- **Response fields used:** `name` (track title), `artist.name`, `playcount`
- **Resilience:** Wrapped in try/except like all other feed fetches — on failure, existing content between markers is preserved

## HTML Structure

New `<!-- music:start/end -->` markers in `index.html`. Section heading is static HTML (not injected). Build injects the `<ul>` contents only.

```html
<section aria-labelledby="music-heading">
  <h2 id="music-heading">Listening to lately</h2>
  <!-- music:start -->
  <ul class="music-list">
    <li class="track">
      <span class="track-title">Track Name</span>
      <span class="track-meta">Artist · 12 plays</span>
    </li>
  </ul>
  <!-- music:end -->
</section>
```

Artist and play count collapsed into a single `track-meta` line — compact and scannable, consistent with how films and articles handle secondary info.

## Build Changes

- New `fetch_lastfm_top_tracks(username, api_key, limit)` function in `build.py`
- New `build_music_html(tracks)` function outputting the `<ul>` block
- Both called in `cmd_build()` alongside existing feed fetches
- `build.py` docstring updated to list Last.fm as a sixth source

## site.toml Changes

```toml
[sources.lastfm]
username = "..."   # Last.fm username (public)
limit = 8
```

## CSS

New styles for `.music-list`, `.track`, `.track-title`, `.track-meta` — following the same conventions as `.films` and `.reading`.

## Layout Impact (Iteration 4)

The existing iteration 4 layout spec (2-col grid: books left, films right) was written before music was planned. With four content sections — books, films, music, articles — the grid needs to be redesigned from scratch as part of iteration 4. The specific arrangement (3-col, 2×2, or asymmetric) is to be determined in iteration 4 planning. This design establishes that music is a peer section alongside the others.

## Roadmap Sequencing

Music is folded into iteration 4 rather than treated as a standalone iteration. Iteration 4 (Layout restructure) will now encompass:
- Content-aware grid redesigned with all four sections in mind
- "Currently reading" callout extraction
- Music section (data pipeline + HTML + CSS)
- Tightened list density

## New GitHub Secret

`LASTFM_API_KEY` — to be added to repo settings alongside existing secrets.
