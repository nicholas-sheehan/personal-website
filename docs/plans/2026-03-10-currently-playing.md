# Iteration 12 — Currently Playing (Live API) Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add a live "Currently playing / Last played" status strip that fetches real-time data from a Cloudflare Worker proxying the Last.fm API.

**Architecture:** A `worker/` directory in the repo contains a Cloudflare Worker that calls Last.fm `user.getRecentTracks?limit=1`, extracts the nowplaying flag, and returns JSON. The static page fetches this Worker on load and polls every 30 seconds. The strip HTML is static in `index.html`; JS reveals and updates it at runtime.

**Tech Stack:** Cloudflare Workers (JS), Wrangler CLI, Last.fm REST API, vanilla JS fetch + setInterval, CSS keyframe animation.

---

## Pre-flight: Cloudflare setup (one-time manual steps)

These are done once by the developer before any code tasks. They are not automatable.

1. Create a free Cloudflare account at https://cloudflare.com
2. Install Wrangler CLI: `npm install -g wrangler`
3. Authenticate: `wrangler login` (opens browser, authorise)
4. Verify: `wrangler whoami` — should print your Cloudflare account name

**Do not proceed to Task 1 until `wrangler whoami` succeeds.**

---

## Task 1: Create the Cloudflare Worker

**Files:**
- Create: `worker/index.js`
- Create: `worker/wrangler.toml`

**Step 1: Create `worker/` directory and `wrangler.toml`**

```toml
# worker/wrangler.toml
name = "now-playing"
main = "index.js"
compatibility_date = "2024-01-01"
```

**Step 2: Create `worker/index.js`**

```js
export default {
  async fetch(request, env) {
    // Handle CORS preflight
    if (request.method === "OPTIONS") return cors(new Response(null, { status: 204 }));

    const url = `https://ws.audioscrobbler.com/2.0/?method=user.getRecentTracks`
              + `&user=tonic-lastfm&limit=1&format=json&api_key=${env.LASTFM_API_KEY}`;

    const res  = await fetch(url);
    const data = await res.json();
    const track = data.recenttracks?.track?.[0];

    if (!track) {
      return cors(Response.json({ nowPlaying: false, track: null, artist: null }));
    }

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

**Step 3: Store the Last.fm API key as a Cloudflare secret**

From the `worker/` directory:
```bash
cd worker
wrangler secret put LASTFM_API_KEY
```
Paste the key when prompted (find it in GitHub Secrets: `LASTFM_API_KEY`). This stores it in Cloudflare — never committed to the repo.

**Step 4: Test the Worker locally**

```bash
wrangler dev
```

Expected output: `Ready on http://localhost:8787`

Open `http://localhost:8787` in a browser. Expected JSON response:
```json
{ "nowPlaying": false, "track": "Some Track", "artist": "Some Artist" }
```
(or `nowPlaying: true` if you happen to be listening right now)

If you see `{"error":...}` from Last.fm, check the API key was set correctly.

**Step 5: Deploy the Worker**

```bash
wrangler deploy
```

Expected output: `Published now-playing (...)` with a URL like `https://now-playing.<your-subdomain>.workers.dev`

Note the Worker URL — you'll need it in Task 4.

**Step 6: Verify the live Worker**

Open the Worker URL in a browser. Confirm JSON is returned (same shape as local test).

**Step 7: Commit Worker files**

```bash
cd ..  # back to repo root
git add worker/
git commit -m "feat: add Cloudflare Worker for Last.fm now-playing proxy"
```

---

## Task 2: Add strip HTML to `index.html`

**Files:**
- Modify: `index.html` (around line 1238, below `<!-- goodreads-now:end -->`)

**Step 1: Locate the insertion point**

Find this block in `index.html`:
```html
<!-- goodreads-now:end -->
          <!-- Currently reading data (hidden — used by status strip above) -->
```

**Step 2: Insert the strip HTML between those two lines**

Add immediately after `<!-- goodreads-now:end -->` and before the `<!-- Currently reading data -->` comment:

```html
          <!-- ── NOW PLAYING STATUS STRIP ── -->
          <div id="now-playing-strip" class="status-strip status-strip--music" aria-live="polite" hidden>
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

**Step 3: Verify the HTML**

Open `index.html` in a browser via `file:///...`. The strip should be invisible (it's `hidden`). No visual change expected yet.

**Step 4: Commit**

```bash
git add index.html
git commit -m "feat: add now-playing strip HTML (hidden, awaiting JS)"
```

---

## Task 3: Add CSS to `style.css`

**Files:**
- Modify: `style.css` (after the existing `NOW READING — Status strip` section, around line 465)

**Step 1: Locate the insertion point**

Find this comment in `style.css`:
```css
/* ──────────────────────────────────────────────
   NOW READING — Status strip
   ────────────────────────────────────────────── */
```

Find the end of that section (the `.status-strip-text em` rule closes around line 465), then locate the next section comment:
```css
/* ──────────────────────────────────────────────
   CONTENT GRID — 2x2 on desktop, 1-col mobile
```

**Step 2: Insert the new CSS between those two sections**

```css
/* ──────────────────────────────────────────────
   NOW PLAYING — Status strip (music / purple variant)
   ────────────────────────────────────────────── */

.status-strip--music {
  background: rgba(168, 85, 247, 0.04);
  border: 1px solid rgba(168, 85, 247, 0.18);
  border-left: 3px solid var(--accent-music);
}

.status-strip--music .status-strip-label {
  color: var(--accent-music);
}

.waveform {
  display: flex;
  align-items: flex-end;
  gap: 2px;
  height: 12px;
  flex-shrink: 0;
}

.waveform-bar {
  width: 2px;
  background: var(--accent-music);
  border-radius: 1px;
  animation: waveform 0.5s ease-in-out infinite alternate;
}

.waveform-bar:nth-child(2) { animation-delay: 0.2s; }
.waveform-bar:nth-child(3) { animation-delay: 0.4s; }

@keyframes waveform {
  from { height: 3px; }
  to   { height: 12px; }
}

/* Static state: last played (not currently live) */
.status-strip--music.is-static .waveform {
  display: none;
}

/* Prevent long track names from overflowing on desktop */
.status-strip-text {
  min-width: 0;
}

@media (prefers-reduced-motion: reduce) {
  .waveform-bar {
    animation: none;
    height: 8px;
  }
}
```

**Step 3: Verify CSS visually**

The build inlines `style.css` into `index.html`. To preview:
```bash
python3 build.py
```
Open `file:///...index.html`. The strip is still hidden (JS not added yet) — no visual change expected. Check dev tools that the new CSS rules are present.

**Step 4: Commit**

```bash
git add style.css
git commit -m "feat: add now-playing strip CSS and waveform animation"
```

---

## Task 4: Add JS to `index.html` and update `site.toml`

**Files:**
- Modify: `index.html` (around line 1524, after the snake script, before `<!-- analytics:start -->`)
- Modify: `site.toml` (add Worker URL reference)

**Step 1: Update `site.toml` with Worker URL**

Add a new `[sources.nowplaying]` section at the end of `site.toml`. Replace `<your-subdomain>` with the actual subdomain shown in `wrangler deploy` output:

```toml
[sources.nowplaying]
# Cloudflare Worker — proxies Last.fm user.getRecentTracks, protects API key
# Deploy: cd worker && wrangler deploy
# Secret: wrangler secret put LASTFM_API_KEY
worker_url = "https://now-playing.<your-subdomain>.workers.dev"
```

**Step 2: Locate the JS insertion point in `index.html`**

Find the snake easter egg script end tag, followed by analytics:
```html
...})();</script>
<!-- analytics:start -->
```

Insert the new script between those two lines.

**Step 3: Add the now-playing IIFE**

Replace `WORKER_URL_HERE` with your actual Worker URL from the `wrangler deploy` output. The Worker URL is **not a secret** — it is a public HTTPS endpoint (the API key never leaves Cloudflare). It is safe to hardcode directly in `index.html`:

```html
<script>(function(){var WORKER='WORKER_URL_HERE';var POLL=30000;var strip=document.getElementById('now-playing-strip');var label=document.getElementById('now-playing-label');var text=document.getElementById('now-playing-text');if(!strip)return;function update(){fetch(WORKER).then(function(r){return r.json();}).then(function(d){if(!d.track)return;text.textContent=d.track+' by '+d.artist;label.textContent=d.nowPlaying?'Now playing':'Last played';strip.classList.toggle('is-static',!d.nowPlaying);strip.removeAttribute('hidden');}).catch(function(){});}update();setInterval(update,POLL);})();</script>
```

Note: the script is minified (one line) to match the style of existing inline scripts in the file.

**Step 4: Run the build to inline updated CSS**

```bash
python3 build.py
```

**Step 5: Verify locally**

Open `file:///...index.html` in a browser. Open dev tools Network tab. You should see a request to your Worker URL. The strip should appear with either:
- Purple "Now playing" label + animating waveform bars + track name
- Purple "Last played" label + no waveform + track name

If the strip doesn't appear, check the console for fetch errors (likely a CORS issue — verify the Worker URL is correct and the Worker is deployed).

**Step 6: Test the "is-static" state**

Temporarily modify the JS in dev tools to pass `d.nowPlaying = false` and confirm the waveform disappears and label reads "Last played". (No permanent code change needed — this is a manual spot-check.)

**Step 7: Test reduced-motion**

In dev tools, check "Emulate CSS media feature prefers-reduced-motion: reduce". Confirm waveform bars stop animating (they freeze at 8px height).

**Step 8: Commit**

```bash
git add index.html site.toml
git commit -m "feat: add now-playing JS fetch + poll, note Worker URL in site.toml"
```

---

## Task 5: Push to staging and review

**Step 1: Restore CI artifacts and pull latest main**

```bash
git restore og-image.png sitemap.xml
git pull --rebase origin main
```

**Step 2: Push the feature branch to staging**

```bash
git push origin main:staging --force-with-lease
```

Wait for the GitHub Actions CI build to complete (check Actions tab). The build runs `python3 build.py` — the now-playing strip HTML and CSS are static, so no build changes expected. The live Worker fetch only happens at runtime.

**Step 3: Pull staging build locally and review**

```bash
git fetch origin staging
git checkout staging
git pull
```

Open `index.html` in a browser. Confirm:
- [ ] Strip appears with purple accent
- [ ] "Now playing" or "Last played" label is correct
- [ ] Waveform animates when now-playing, hidden when last-played
- [ ] Strip polls (wait 30s, if track changes it should update)
- [ ] No console errors

**Step 4: Check back to main for PR**

```bash
git checkout main
```

---

## Task 6: Open PR and merge to main

**Step 1: Download gh CLI if not present**

```bash
/tmp/gh/gh --version 2>/dev/null || (mkdir -p /tmp/gh && curl -sL https://github.com/cli/cli/releases/download/v2.45.0/gh_2.45.0_macOS_arm64.tar.gz | tar -xz -C /tmp/gh --strip-components=2 gh_2.45.0_macOS_arm64/bin/gh)
```

**Step 2: Create PR**

```bash
/tmp/gh/gh pr create \
  --title "feat: iteration 12 — currently playing (live API)" \
  --body "$(cat <<'EOF'
## Summary

- Cloudflare Worker in `worker/` proxies Last.fm `user.getRecentTracks` (API key stored as Cloudflare secret, never in source)
- Purple "Currently playing / Last played" status strip below now-reading strip
- Animating CSS waveform icon (3 bars, staggered `@keyframes`) — hidden for "last played" state
- Fetches on page load + polls every 30s; silent fail keeps strip hidden

## Test plan

- [ ] Strip appears with purple accent on staging
- [ ] "Now playing" label + waveform when track playing
- [ ] "Last played" label + no waveform when nothing playing
- [ ] Strip polls and updates without page refresh
- [ ] `prefers-reduced-motion` suppresses waveform animation
- [ ] Worker URL is not an exposed secret (key is in Cloudflare)

🤖 Generated with [Claude Code](https://claude.com/claude-code)
EOF
)" \
  --base main \
  --head staging
```

**Step 3: Merge the PR**

Review the diff in GitHub. Merge via squash (the only allowed merge strategy). CI builds and deploys on merge to main.

---

## Task 7: Update docs

**Files:**
- Modify: `docs/roadmap.md` — mark iteration 12 ✅
- Modify: `docs/architecture.md` — add Cloudflare Worker to diagram
- Modify: `README.md` — add nowplaying Worker to sources table and note Cloudflare secret is local-only (not GitHub Secrets)
- Modify: `build.py` docstring — note source count unchanged (Worker is runtime, not build-time)
- Update `MEMORY.md` — Data Sources table, Key Files, Gotchas

**Step 1: Mark iteration 12 complete in `docs/roadmap.md`**

Change `⬜ planned` to `✅ shipped YYYY-MM-DD` and tick all checkboxes.

**Step 2: Update `docs/architecture.md`**

Add a `CloudflareWorker` node to the Mermaid diagram:
- `Browser JS` → `CloudflareWorker["Cloudflare Worker\nnow-playing.***.workers.dev"]` → `LastFM`
- Label the browser→worker edge "fetch on load + poll 30s"
- Note: the Worker is a separate deploy from the static site

**Step 3: Update `README.md`**

Add a row to the data sources table:

| Last.fm (now playing) | Live track via Cloudflare Worker | `LASTFM_API_KEY` (Cloudflare secret, not GitHub) |

**Step 4: Commit docs**

```bash
git add docs/roadmap.md docs/architecture.md README.md
git commit -m "docs: mark iteration 12 complete, update architecture and README"
git push origin main
```
