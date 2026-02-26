# Iteration 8 Design — Boot Sequence + Snake Easter Egg

**Date:** 2026-02-26
**Status:** Approved

---

## Overview

Two theatrical features that deepen the Y2K / PS2 Memory Card aesthetic:

1. **Randomised boot sequence** — replaces the current static 2-line boot overlay with a JS-driven sequence of fake system-check messages, picked randomly per load.
2. **Snake easter egg** — a fullscreen Snake game triggered by typing `TONIC` on a keyboard.

Both are implemented as static inline `<script>` blocks in `index.html`, outside any `<!-- marker -->` pairs, so CI builds never touch them. No changes to `build.py`.

---

## Feature 1: Randomised Boot Sequence

### Behaviour

- JS picks 5–6 messages at random from a pool of 21.
- Messages appear one per 400ms, injected into the `.boot-overlay` div as `<p>` elements.
- After the last message + 400ms hold, the overlay fades out (300ms transition).
- `<main>` becomes visible after the fade-out completes (~3.1s total).
- `prefers-reduced-motion`: all messages injected at once, 200ms hold, done. No delays.

### CSS changes

The current CSS keyframe animation on `.boot-overlay` is replaced with a `transition`:

```css
/* Before */
animation: boot-overlay-lifecycle 900ms ease-in-out forwards;

/* After */
opacity: 0;
transition: opacity 300ms ease;
```

JS adds `.boot--visible` (opacity 1) and `.boot--done` (opacity 0, pointer-events none) classes.

The current `main` animation (`main-reveal 0s 800ms forwards`) is removed. JS sets `main.style.visibility = 'visible'` after fade-out. If JS fails entirely, a CSS fallback ensures `<main>` becomes visible after 1s.

`.boot-overlay-line--dim` class is retired (no longer needed — all lines are the same style).

### Message pool (21 messages)

```
INIT BIOS REV 3.11.0...............[ OK ]
CHECKING MEMORY (8192 MB)..........[ OK ]
LOADING KERNEL v6.6.0..............[ OK ]
MOUNTING /dev/sda1.................[ OK ]
MOUNTING /dev/shm..................[ OK ]
FSCK: NO ERRORS FOUND..............[ OK ]
SYNCING HARDWARE CLOCK.............[ OK ]
CHECKING ENTROPY POOL..............[ OK ]
LOADING MODULE: display............[ OK ]
LOADING MODULE: network............[ OK ]
LOADING MODULE: input..............[ OK ]
LOADING MODULE: audio..............[ OK ]
ALLOCATING FRAMEBUFFER (1920x1080).[ OK ]
CALIBRATING CRT SCANLINES..........[ OK ]
STARTING NETWORK MANAGER...........[ OK ]
ESTABLISHING UPLINK................[DONE]
WARMING PHOSPHOR TUBES.............[ OK ]
VERIFYING CHECKSUMS: PASS..........[ OK ]
FLUSHING WRITE BUFFER...............[DONE]
AUTHENTICATING SESSION.............[ OK ]
QUEUEING UP DATABANK...............[ OK ]
```

### JS structure

```js
(function () {
  var MESSAGES = [ /* 21 messages */ ];
  var overlay = document.querySelector('.boot-overlay');
  var main = document.querySelector('main');
  var reduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  // Pick 5–6 at random
  // If reduced: inject all at once, 200ms hold, done
  // Else: fade in overlay, inject messages 400ms apart, fade out, reveal main
})();
```

The script tag sits immediately after the closing `</div>` of `.boot-overlay`.

### Progressive enhancement fallback

A `<noscript>`-compatible CSS rule ensures `<main>` is always visible after 1s if JS never runs:

```css
@keyframes main-reveal-fallback {
  to { visibility: visible; }
}
main {
  visibility: hidden;
  animation: main-reveal-fallback 0s 1s forwards;
}
```

JS removes this animation before taking control.

---

## Feature 2: Snake Easter Egg

*(Deferred — implementation planned separately)*

### Trigger

`keydown` listener buffers last 5 keys. Matches `TONIC` (case-insensitive). Skipped on touch-primary devices (`pointer: coarse` media query check on init).

### Overlay

`position: fixed; inset: 0; z-index: 99999; background: var(--bg)`. Created and appended to `<body>` on first trigger. `<canvas>` fills it.

### Game

- 20×20 grid; cell size auto-calculated from viewport.
- Snake = blue (`--accent: #3b82f6`), food = green (`--accent-books: #22c55e`), bg = `--bg`.
- Speed: 150ms/tick → ramps to ~80ms at score 10+.
- Dies on wall or self-collision.
- Score shown top-left in monospace.
- No high score persistence (session score only).

### Controls

- Arrow keys to steer.
- ESC: exit game at any time.
- ENTER (on game-over screen): restart.
- Mobile: not supported (easter egg silently disabled on touch devices).

### Game over

Overlay dims. Centred canvas text: `GAME OVER` / `SCORE: X` / `[ ESC ] EXIT   [ ENTER ] RESTART`.

---

## Files affected

| File | Change |
|------|--------|
| `style.css` | Boot overlay: animation → transition. Main: animation → static hidden + fallback. Snake overlay CSS (deferred). |
| `index.html` | Clear static boot lines. Add boot `<script>` after overlay div. Add snake `<script>` before `</body>` (deferred). |
| `build.py` | No changes. |
| `.github/workflows/build.yml` | No changes. |
