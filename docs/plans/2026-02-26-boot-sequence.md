# Boot Sequence Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Replace the static 2-line CSS boot overlay with a JS-driven sequence of 5–6 randomly selected fake system-check messages that appear sequentially over ~3 seconds.

**Architecture:** CSS animation on `.boot-overlay` is replaced with a CSS transition (opacity). A static inline `<script>` block (placed before `</body>`, outside all `<!-- marker -->` pairs) picks messages at random and drives the timing via `setTimeout`. `<main>` stays `visibility: hidden` until JS reveals it; a CSS fallback ensures it appears after 1s if JS never runs.

**Tech Stack:** Vanilla JS (ES5-compatible, no deps), CSS transitions, `build.py` (to re-inline `style.css` into `index.html` after CSS edits).

---

## Context for implementors

- `style.css` is the CSS source file. It is injected between `<!-- style:start/end -->` in `index.html` by `build.py`. **Always edit `style.css` first, then run `python3 build.py` to update the inlined style.**
- Static HTML in `index.html` that is outside any `<!-- marker:start/end -->` pair (e.g. the `.boot-overlay` div, the inline JS blocks near `</body>`) **survives every build untouched.**
- The JS `<script>` block goes between the existing timestamp JS block (line ~1383) and `<!-- analytics:start -->` — same zone as the existing inline JS.
- There is no test framework. Verification is done by opening `index.html` in a browser.
- Local Python is 3.9. Run builds as `python3 build.py` (no secrets needed for CSS-only changes — the build won't fail on missing API keys for CSS injection).

---

## Task 1: CSS — replace animation with transition

**Files:**
- Modify: `style.css` (boot overlay section, ~lines 79–162)
- Run: `python3 build.py` to re-inline into `index.html`

### Step 1: Edit `style.css` — remove old boot keyframes and update `.boot-overlay`

Find the boot animation block (search for `boot-overlay-lifecycle`). Replace the entire boot section with the following:

```css
/* ──────────────────────────────────────────────
   BOOT ANIMATION — JS-driven. CSS provides the
   transition envelope; JS controls opacity timing.
   Fallback: main becomes visible after 1s if JS
   never runs.
   ────────────────────────────────────────────── */

@keyframes boot-cursor-blink {
  0%, 49%  { opacity: 1; }
  50%, 100% { opacity: 0; }
}

@keyframes main-reveal-fallback {
  to { visibility: visible; }
}

/* The full-screen boot overlay */
.boot-overlay {
  position: fixed;
  inset: 0;
  z-index: 10000;
  background: var(--bg);
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  justify-content: center;
  padding: 3rem 4rem;
  opacity: 0;
  transition: opacity 300ms ease;
  pointer-events: none;
}

.boot-overlay-line {
  font-family: var(--font-mono);
  font-size: 0.75rem;
  font-weight: 500;
  color: var(--accent);
  letter-spacing: 0.16em;
  text-transform: uppercase;
  line-height: 1.8;
}

.boot-cursor {
  display: inline-block;
  width: 0.55em;
  height: 1em;
  background: var(--accent);
  margin-left: 0.15em;
  vertical-align: text-bottom;
  animation: boot-cursor-blink 500ms step-end infinite;
}

/* Main content: hidden until JS reveals it.
   Fallback: becomes visible after 1s if JS never runs. */
main {
  visibility: hidden;
  animation: main-reveal-fallback 0s 1s forwards;
}
```

**What changed vs before:**
- Removed `@keyframes boot-overlay-lifecycle` (was the full CSS animation)
- Removed `@keyframes main-reveal` (was the 0s delay reveal)
- Removed `.boot-overlay-line--dim` rule (no longer used — all injected lines share one style)
- `.boot-overlay` now uses `opacity: 0; transition: opacity 300ms ease` instead of the keyframe animation
- `main` now has a 1s CSS fallback animation (no-JS safety net)

### Step 2: Run the build to re-inline the CSS

```bash
cd "/Users/nicholassheehan/Documents/Claude Files/Personal website"
python3 build.py
```

Expected: Build completes. It will print warnings about missing API keys — that's fine. The inline `<style>` block in `index.html` (between `<!-- style:start/end -->`) now contains the updated CSS.

### Step 3: Verify in browser

Open `index.html` in a browser. You should see:
- A blank dark screen (overlay at opacity 0, main hidden) — this is expected
- After 1s, main content becomes visible (CSS fallback kicking in)
- No visible boot animation yet — JS hasn't been added

### Step 4: Commit

```bash
git add style.css index.html
git commit -m "feat: replace boot overlay CSS animation with JS-driven transition"
```

---

## Task 2: HTML — clear static boot lines from overlay

**Files:**
- Modify: `index.html` (~line 1015)

### Step 1: Locate the `.boot-overlay` div

Find this block in `index.html`:

```html
  <!-- Boot overlay — aria-hidden so screen readers skip it -->
  <div class="boot-overlay" aria-hidden="true" role="presentation">
    <p class="boot-overlay-line">System: Nic Sheehan</p>
    <p class="boot-overlay-line boot-overlay-line--dim">Establishing connection...<span class="boot-cursor"></span></p>
  </div>
```

### Step 2: Clear the static lines, leave the div empty

Replace with:

```html
  <!-- Boot overlay — aria-hidden so screen readers skip it -->
  <!-- Lines are injected by the boot-sequence script below -->
  <div class="boot-overlay" aria-hidden="true" role="presentation"></div>
```

### Step 3: Verify the page still loads

Open `index.html` in a browser. The overlay is now empty. After 1s the main content appears (CSS fallback). No visual regression.

### Step 4: Commit

```bash
git add index.html
git commit -m "chore: clear static boot overlay lines (will be JS-injected)"
```

---

## Task 3: JS — add the boot sequence script

**Files:**
- Modify: `index.html` — add `<script>` block between the timestamp JS block and `<!-- analytics:start -->`

### Step 1: Locate the insertion point

Find this section near the bottom of `index.html`:

```html
<script>(function(){var b=document.querySelector('.colophon-buildtime');...})();</script>
<!-- analytics:start -->
```

### Step 2: Insert the boot sequence script between them

Add the following `<script>` block between the timestamp script and `<!-- analytics:start -->`:

```html
<script>(function(){var M=['INIT BIOS REV 3.11.0...............[ OK ]','CHECKING MEMORY (8192 MB)..........[ OK ]','LOADING KERNEL v6.6.0..............[ OK ]','MOUNTING /dev/sda1.................[ OK ]','MOUNTING /dev/shm..................[ OK ]','FSCK: NO ERRORS FOUND..............[ OK ]','SYNCING HARDWARE CLOCK.............[ OK ]','CHECKING ENTROPY POOL..............[ OK ]','LOADING MODULE: display............[ OK ]','LOADING MODULE: network............[ OK ]','LOADING MODULE: input..............[ OK ]','LOADING MODULE: audio..............[ OK ]','ALLOCATING FRAMEBUFFER (1920x1080).[ OK ]','CALIBRATING CRT SCANLINES..........[ OK ]','STARTING NETWORK MANAGER...........[ OK ]','ESTABLISHING UPLINK................[DONE]','WARMING PHOSPHOR TUBES.............[ OK ]','VERIFYING CHECKSUMS: PASS..........[ OK ]','FLUSHING WRITE BUFFER..............[DONE]','AUTHENTICATING SESSION.............[ OK ]','QUEUEING UP DATABANK...............[ OK ]'];var o=document.querySelector('.boot-overlay');var mn=document.querySelector('main');if(!o||!mn)return;mn.style.animation='none';var reduced=window.matchMedia('(prefers-reduced-motion: reduce)').matches;var pool=M.slice();for(var i=pool.length-1;i>0;i--){var j=Math.floor(Math.random()*(i+1));var t=pool[i];pool[i]=pool[j];pool[j]=t;}var count=5+Math.round(Math.random());var chosen=pool.slice(0,count);function addLine(txt){var p=document.createElement('p');p.className='boot-overlay-line';p.textContent=txt;o.appendChild(p);}function fadeOut(){o.style.opacity='0';setTimeout(function(){o.style.display='none';mn.style.visibility='visible';},300);}if(reduced){chosen.forEach(addLine);o.style.opacity='1';setTimeout(fadeOut,200);return;}requestAnimationFrame(function(){requestAnimationFrame(function(){o.style.opacity='1';});});var d=300;chosen.forEach(function(msg){setTimeout(function(){addLine(msg);},d);d+=400;});setTimeout(fadeOut,d+400);})();</script>
```

### Step 3: Readable reference version (do not commit this — for your understanding only)

```js
(function () {
  var MESSAGES = [
    'INIT BIOS REV 3.11.0...............[ OK ]',
    'CHECKING MEMORY (8192 MB)..........[ OK ]',
    'LOADING KERNEL v6.6.0..............[ OK ]',
    'MOUNTING /dev/sda1.................[ OK ]',
    'MOUNTING /dev/shm..................[ OK ]',
    'FSCK: NO ERRORS FOUND..............[ OK ]',
    'SYNCING HARDWARE CLOCK.............[ OK ]',
    'CHECKING ENTROPY POOL..............[ OK ]',
    'LOADING MODULE: display............[ OK ]',
    'LOADING MODULE: network............[ OK ]',
    'LOADING MODULE: input..............[ OK ]',
    'LOADING MODULE: audio..............[ OK ]',
    'ALLOCATING FRAMEBUFFER (1920x1080).[ OK ]',
    'CALIBRATING CRT SCANLINES..........[ OK ]',
    'STARTING NETWORK MANAGER...........[ OK ]',
    'ESTABLISHING UPLINK................[DONE]',
    'WARMING PHOSPHOR TUBES.............[ OK ]',
    'VERIFYING CHECKSUMS: PASS..........[ OK ]',
    'FLUSHING WRITE BUFFER..............[DONE]',
    'AUTHENTICATING SESSION.............[ OK ]',
    'QUEUEING UP DATABANK...............[ OK ]'
  ];

  var overlay = document.querySelector('.boot-overlay');
  var main = document.querySelector('main');

  if (!overlay || !main) return;

  // Cancel CSS fallback — JS is now in control
  main.style.animation = 'none';

  var reduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  // Fisher-Yates shuffle, then take 5 or 6
  var pool = MESSAGES.slice();
  for (var i = pool.length - 1; i > 0; i--) {
    var j = Math.floor(Math.random() * (i + 1));
    var tmp = pool[i]; pool[i] = pool[j]; pool[j] = tmp;
  }
  var count = 5 + Math.round(Math.random()); // 5 or 6
  var chosen = pool.slice(0, count);

  function addLine(text) {
    var p = document.createElement('p');
    p.className = 'boot-overlay-line';
    p.textContent = text;
    overlay.appendChild(p);
  }

  function fadeOut() {
    overlay.style.opacity = '0';
    setTimeout(function () {
      overlay.style.display = 'none';
      main.style.visibility = 'visible';
    }, 300); // matches CSS transition duration
  }

  // prefers-reduced-motion: show all at once, 200ms hold, done
  if (reduced) {
    chosen.forEach(addLine);
    overlay.style.opacity = '1';
    setTimeout(fadeOut, 200);
    return;
  }

  // Normal path: fade in, inject messages sequentially, then fade out
  // Double rAF ensures transition fires (avoids same-frame collapse)
  requestAnimationFrame(function () {
    requestAnimationFrame(function () {
      overlay.style.opacity = '1';
    });
  });

  var delay = 300; // start after fade-in completes
  chosen.forEach(function (msg) {
    setTimeout(function () { addLine(msg); }, delay);
    delay += 400;
  });

  // 400ms hold after last message, then fade out
  setTimeout(fadeOut, delay + 400);
})();
```

### Step 4: Verify in browser — normal path

Open `index.html`. You should see:
- Black screen, then overlay fades in (~300ms)
- 5 or 6 system-check messages appear one at a time, 400ms apart
- Overlay fades out
- Main content becomes visible
- Total duration: ~3.1s

Reload several times to confirm different message combinations appear.

### Step 5: Verify — prefers-reduced-motion

In Chrome DevTools → Rendering → "Emulate CSS media feature prefers-reduced-motion: reduce".

Reload. You should see:
- All messages appear instantly
- Brief hold (~200ms)
- Overlay fades out immediately
- Main content visible

### Step 6: Commit

```bash
git add index.html
git commit -m "feat: add randomised JS boot sequence (21 messages, pick 5-6 per load)"
```

---

## Task 4: Push and verify CI

### Step 1: Pull before push (Actions bot commits frequently)

```bash
git pull --rebase origin main
```

If a rebase conflict appears on `index.html` in the `<!-- updated:start/end -->` block (the timestamp), resolve by keeping OUR version of the surrounding HTML but accepting the bot's timestamp text, then `git rebase --continue`.

### Step 2: Push

```bash
git push origin main
```

### Step 3: Watch the CI build

Go to the Actions tab in the GitHub repo. The build-and-deploy workflow should complete successfully. Once done, visit `https://www.nicsheehan.com` and verify the boot sequence runs in production.

### Step 4: Update roadmap

Mark iteration 8 boot sequence item as complete in `docs/roadmap.md`:

```markdown
- [x] Randomised boot sequence — pool of ~20 quirky messages, pick 4–6 per load, display sequentially with `[ OK ]` / `[DONE]` suffixes
```

Commit:

```bash
git add docs/roadmap.md
git commit -m "docs: mark iteration 8 boot sequence complete"
git push origin main
```
