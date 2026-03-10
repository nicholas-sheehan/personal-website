# Iteration 12 — Currently Playing (Live API)

**Date:** 2026-03-10
**Status:** Approved, ready for implementation

---

## Overview

First live data source for the site. A Cloudflare Worker proxies the Last.fm `user.getRecentTracks` API (protecting the API key), and the static page fetches it on load then polls every 30 seconds. A "Currently playing" status strip appears below the now-reading strip, using the purple music accent and an animating CSS waveform icon.

---

## Architecture

```
Browser JS
  └─ fetch("https://now-playing.nicsheehan.workers.dev")
       └─ Cloudflare Worker
            └─ Last.fm user.getRecentTracks?limit=1
```

- Worker is deployed independently from the static site (`wrangler deploy`)
- `LASTFM_API_KEY` stored as a Cloudflare secret — never in source
- CORS locked to `https://www.nicsheehan.com`
- Worker lives in `worker/` subdirectory of this repo
- Worker URL noted in `site.toml` as a comment (not used at build time)

### Worker response shape

```json
{ "nowPlaying": true,  "track": "Fade to Black", "artist": "Metallica" }
{ "nowPlaying": false, "track": "...",            "artist": "..." }
```

When `nowPlaying: false`, the strip shows "Last played" as the label (last scrobbled track). If the Worker is unreachable or returns an error, the strip stays hidden silently.

---

## HTML

Static in `index.html`, placed directly below `<!-- goodreads-now:end -->`. No build-time injection — JS populates it at runtime.

```html
<div id="now-playing-strip" class="status-strip status-strip--music" hidden>
  <span class="status-strip-label" id="now-playing-label">Now playing</span>
  <span class="waveform" aria-hidden="true">
    <span class="waveform-bar"></span>
    <span class="waveform-bar"></span>
    <span class="waveform-bar"></span>
  </span>
  <span class="status-strip-sep">›</span>
  <span class="status-strip-text" id="now-playing-text"></span>
</div>
```

- `hidden` by default — removed on first successful fetch
- `.status-strip--music` modifier overrides green accent with purple
- Waveform: 3 `<span>` bars, each animated with staggered `animation-delay`
- Strip is display-only — no link

---

## CSS

Added to `style.css`. Existing `.status-strip` (green, now-reading) is untouched.

```css
/* Purple variant for currently-playing strip */
.status-strip--music {
  background: rgba(168, 85, 247, 0.04);
  border: 1px solid rgba(168, 85, 247, 0.18);
  border-left: 3px solid var(--accent-music);
}

.status-strip--music .status-strip-label {
  color: var(--accent-music);
}

/* Waveform icon */
.waveform {
  display: flex;
  align-items: flex-end;
  gap: 2px;
  height: 12px;
}

.waveform-bar {
  width: 2px;
  background: var(--accent-music);
  border-radius: 1px;
  animation: waveform 0.8s ease-in-out infinite alternate;
}

.waveform-bar:nth-child(2) { animation-delay: 0.2s; }
.waveform-bar:nth-child(3) { animation-delay: 0.4s; }

@keyframes waveform {
  from { height: 3px; }
  to   { height: 12px; }
}

/* Static state (last played — not live) */
.status-strip--music.is-static .waveform {
  display: none;
}

@media (prefers-reduced-motion: reduce) {
  .waveform-bar { animation: none; height: 8px; }
}
```

---

## JavaScript

Inline IIFE in `index.html`, alongside existing boot/countdown scripts.

```js
(function () {
  const WORKER_URL = "https://now-playing.nicsheehan.workers.dev";
  const POLL_MS = 30_000;
  const strip = document.getElementById("now-playing-strip");
  const label = document.getElementById("now-playing-label");
  const text  = document.getElementById("now-playing-text");

  function update() {
    fetch(WORKER_URL)
      .then(r => r.json())
      .then(data => {
        text.textContent = `${data.track} by ${data.artist}`;
        label.textContent = data.nowPlaying ? "Now playing" : "Last played";
        strip.classList.toggle("is-static", !data.nowPlaying);
        strip.removeAttribute("hidden");
      })
      .catch(() => {}); // silent fail — strip stays hidden
  }

  update();
  setInterval(update, POLL_MS);
})();
```

---

## Worker

`worker/index.js`:

```js
export default {
  async fetch(request, env) {
    if (request.method === "OPTIONS") return cors(new Response(null, { status: 204 }));

    const url = `https://ws.audioscrobbler.com/2.0/?method=user.getRecentTracks`
              + `&user=tonic-lastfm&limit=1&format=json&api_key=${env.LASTFM_API_KEY}`;

    const res  = await fetch(url);
    const data = await res.json();
    const track = data.recenttracks?.track?.[0];

    if (!track) return cors(Response.json({ nowPlaying: false, track: null, artist: null }));

    return cors(Response.json({
      nowPlaying: track["@attr"]?.nowplaying === "true",
      track:  track.name,
      artist: track.artist["#text"],
    }));
  }
};

function cors(r) {
  const h = new Headers(r.headers);
  h.set("Access-Control-Allow-Origin", "https://www.nicsheehan.com");
  h.set("Access-Control-Allow-Methods", "GET, OPTIONS");
  return new Response(r.body, { status: r.status, headers: h });
}
```

`worker/wrangler.toml`:

```toml
name = "now-playing"
main = "index.js"
compatibility_date = "2024-01-01"
```

---

## One-time Cloudflare setup (not code)

1. Create Cloudflare account at cloudflare.com
2. `npm install -g wrangler`
3. `wrangler login`
4. `wrangler secret put LASTFM_API_KEY` (from `worker/` dir)
5. `wrangler deploy` (from `worker/` dir)

---

## Out of scope

- Clicking the strip to link to Last.fm — display only
- Album art or album name in the strip
- Caching at the Worker layer (Last.fm is fast enough, and the Worker runs per-request)
