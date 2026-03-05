# Iteration 11 — Visual Polish & Modal Improvements

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add a warm-up animation after boot, improve the detail modal (size, meta layout, navigation, close position), and add a Last.fm footer link to the music panel.

**Architecture:** Pure frontend — CSS + HTML + JS only. CSS lives in `style.css` and gets inlined into `index.html` at build time via `python3 build.py`. JS lives as inline `<script>` blocks directly in `index.html`. No `build.py` logic changes.

**Tech Stack:** Vanilla CSS (keyframes, filter, flexbox), vanilla JS (DOM manipulation, event handling), Python 3.9 build script (to re-inline CSS changes).

> **Before coding:** Pass this plan to the frontend designer agent for a visual review pass. Incorporate any feedback before starting Task 1.

---

## How to test changes

CSS changes in `style.css` must be re-inlined before they take effect in the browser:

```bash
cd "/Users/nicholassheehan/Documents/Claude Files/Personal website"
python3 build.py
```

Then open `index.html` in a browser. JS changes in `index.html` are immediate (no build step needed — but run build.py anyway to keep the inline CSS in sync).

---

### Task 1: Last.fm footer link

The simplest change — adds a static footer link to the music panel, matching the pattern already used by Books (→ Goodreads) and Films (→ Letterboxd). Resolves the bottom panel height mismatch.

**Files:**
- Modify: `index.html` (music panel section, after `<!-- music:end -->`)

**Step 1: Locate the insertion point**

In `index.html`, find this block (around line 1375):

```html
<!-- music:end -->
              </div>
            </section>
```

**Step 2: Add the static footer**

Replace the above with:

```html
<!-- music:end -->
              </div>
              <footer class="panel-footer">
                <a href="https://www.last.fm/user/tonic-lastfm" class="panel-footer-link" target="_blank" rel="noopener noreferrer">→ Last.fm</a>
              </footer>
            </section>
```

Note: this is outside the `<!-- music:start/end -->` markers, so it survives CI rebuilds.

**Step 3: Verify**

Open `index.html` in a browser. The Music panel should now have a `→ Last.fm` link at the bottom, vertically aligned with the `→ Goodreads` and `→ Letterboxd` links on the adjacent panels.

**Step 4: Commit**

```bash
git add index.html
git commit -m "feat: add Last.fm profile footer link to music panel"
```

---

### Task 2: Warm-up animation — CSS

Adds the keyframe animation and class to `style.css`. The animation eases the entire `<main>` from blurred/dim to clear over 3 seconds after boot.

**Files:**
- Modify: `style.css`

**Step 1: Add the keyframe and class**

Find the boot overlay block near the top of `style.css` (around line 86). After the `.boot-overlay-line` rule, add:

```css
/* Warm-up animation: screen dialling in after boot */
@keyframes warmup {
  0%   { filter: blur(4px) brightness(0.4); }
  60%  { filter: blur(1px) brightness(0.9); }
  100% { filter: blur(0)   brightness(1);   }
}

.warming-up {
  animation: warmup 3s ease-out forwards;
}

@media (prefers-reduced-motion: reduce) {
  .warming-up { animation: none; }
}
```

**Step 2: Re-inline the CSS**

```bash
python3 build.py
```

Expected: build completes, `index.html` updated with new inline CSS. The `.warming-up` class and `@keyframes warmup` should now appear in the `<style>` block in `index.html`.

Verify with:
```bash
grep -c "warmup" index.html
```
Expected: `2` (keyframe definition + class rule).

**Step 3: Commit**

```bash
git add style.css index.html
git commit -m "feat: add warm-up animation CSS (blur/brightness ease-out)"
```

---

### Task 3: Warm-up animation — JS trigger

Hooks the warm-up class into the existing boot sequence JS so it fires when the boot overlay fades.

**Files:**
- Modify: `index.html` (boot sequence `<script>` block, around line 1468)

**Step 1: Find the boot JS**

In `index.html`, find the boot sequence IIFE (starts with `(function(){var M=[...`). Locate the `fadeOut` function:

```javascript
function fadeOut(){o.style.opacity="0";setTimeout(function(){o.style.display="none";mn.style.visibility="visible";},300);}
```

**Step 2: Update fadeOut to trigger warm-up**

Replace with:

```javascript
function fadeOut(){o.style.opacity="0";setTimeout(function(){o.style.display="none";mn.style.animation="";mn.style.visibility="visible";mn.classList.add("warming-up");},300);}
```

The two additions:
- `mn.style.animation=""` — clears the inline `animation: none` that was set at boot start (to suppress the CSS fallback animation). Without this, the inline style overrides the class-based warm-up animation.
- `mn.classList.add("warming-up")` — triggers the animation.

**Step 3: Verify**

Open `index.html` in a browser. After the boot overlay fades, the page content should visibly blur and dim then ease into clarity over ~3 seconds. Check that:
- Animation runs on normal load
- No animation flicker if the page is reloaded mid-animation
- With `prefers-reduced-motion` enabled in OS settings (or browser DevTools), the animation does not run

**Step 4: Commit**

```bash
git add index.html
git commit -m "feat: trigger warm-up animation from boot JS"
```

---

### Task 4: Last.fm footer link

Already done in Task 1 — skip.

---

### Task 5: Modal close button — move to right

Moves `[ X ]` from first child (left) to last child (right) of `.modal-header`. No CSS changes needed — the existing flex layout already puts last children on the right.

**Files:**
- Modify: `index.html` (modal HTML, around line 1474)

**Step 1: Find the modal header HTML**

Locate this block:

```html
<div class="modal-header">
  <button class="modal-close" aria-label="Close">[ X ]</button>
  <span class="modal-type-label" aria-hidden="true"></span>
  <span class="modal-index" aria-hidden="true"></span>
</div>
```

**Step 2: Reorder — close button moves to last**

Replace with:

```html
<div class="modal-header">
  <span class="modal-type-label" aria-hidden="true"></span>
  <span class="modal-index" aria-hidden="true"></span>
  <button class="modal-close" aria-label="Close">[ X ]</button>
</div>
```

Note: The modal navigation group (Task 7) will replace `<span class="modal-index">` — so this intermediate state is temporary, but keeping index here avoids breaking the modal display between tasks.

**Step 3: Update the tab trap**

The existing tab trap in the modal JS loops between `focusable[0]` and `focusable[last]`. Moving the close button to last means it's now the last focusable element (instead of first). The tab trap code does not hardcode order — it uses `querySelectorAll('button, a[href]')` — so **no JS change is needed**. Verify this is the case by reading the tab trap block.

**Step 4: Verify**

Open `index.html`, click any panel row to open the modal. The `[ X ]` button should appear on the far right of the header bar. Tab focus should still cycle correctly within the modal.

**Step 5: Commit**

```bash
git add index.html
git commit -m "feat: move modal close button to top-right"
```

---

### Task 6: Modal size + full synopsis

Widens the modal and removes the 4-line text clamp on descriptions.

**Files:**
- Modify: `style.css`

**Step 1: Update modal max-width**

Find `.modal-box` (around line 971):

```css
.modal-box {
  background: var(--panel);
  border-top: 4px solid var(--modal-accent, var(--accent));
  max-width: 400px;
  ...
```

Change `max-width: 400px` to `max-width: 560px`.

**Step 2: Remove line-clamp from `.modal-desc`**

Find `.modal-desc` (around line 1074). Remove these three lines:

```css
  display: -webkit-box;
  -webkit-line-clamp: 4;
  -webkit-box-orient: vertical;
  overflow: hidden;
```

The result should be:

```css
.modal-desc {
  font-size: 0.7rem;
  color: var(--text-tertiary);
  margin: 0;
  line-height: 1.5;
}
```

**Step 3: Re-inline and verify**

```bash
python3 build.py
```

Open `index.html` and click a book or film row. The modal should be visibly wider (560px max) and the description should show in full without truncation.

**Step 4: Commit**

```bash
git add style.css index.html
git commit -m "feat: widen modal to 560px, remove description line-clamp"
```

---

### Task 7: Modal meta hierarchy — CSS + HTML

Splits the single meta line into two: source data (secondary colour) and personal data (panel accent colour).

**Files:**
- Modify: `style.css` (replace `.modal-meta` with two new rules)
- Modify: `index.html` (modal HTML + JS)

**Step 1: Update CSS**

In `style.css`, find and replace the entire `.modal-meta` rule (around line 1067):

```css
.modal-meta {
  font-size: 0.7rem;
  color: var(--text-secondary);
  margin: 0;
  line-height: 1.4;
}
```

Replace with:

```css
.modal-meta-source {
  font-size: 0.7rem;
  color: var(--text-secondary);
  margin: 0;
  line-height: 1.4;
}

.modal-meta-personal {
  font-size: 0.7rem;
  color: var(--modal-accent, var(--accent));
  margin: 0;
  line-height: 1.4;
}
```

**Step 2: Re-inline CSS**

```bash
python3 build.py
```

**Step 3: Update modal HTML**

In `index.html`, find the modal body:

```html
<div class="modal-body">
  <h2 class="modal-title" id="modal-title"></h2>
  <p class="modal-meta"></p>
  <p class="modal-desc" hidden></p>
  <a class="modal-link" target="_blank" rel="noopener noreferrer"></a>
</div>
```

Replace with:

```html
<div class="modal-body">
  <h2 class="modal-title" id="modal-title"></h2>
  <p class="modal-meta-source"></p>
  <p class="modal-meta-personal" hidden></p>
  <p class="modal-desc" hidden></p>
  <a class="modal-link" target="_blank" rel="noopener noreferrer"></a>
</div>
```

**Step 4: Update modal JS — openModal()**

In the modal IIFE (`<script>` block after the modal HTML), update the variable declarations at the top:

Find:
```javascript
var metaEl = overlay.querySelector('.modal-meta');
```

Replace with:
```javascript
var metaSourceEl = overlay.querySelector('.modal-meta-source');
var metaPersonalEl = overlay.querySelector('.modal-meta-personal');
```

Then update the per-type meta assembly. Find the block starting `var meta = '', desc = '', linkText = '';` and replace the entire meta/desc/link block with:

```javascript
var metaSource = '', metaPersonal = '', desc = '', linkText = '';

if (type === 'book') {
  metaSource = row.dataset.author || '';
  var bookPersonalParts = [row.dataset.stars, row.dataset.finished].filter(Boolean);
  metaPersonal = bookPersonalParts.join(' · ');
  desc = row.dataset.description || '';
  linkText = '→ View on Goodreads';
} else if (type === 'film') {
  var director = row.dataset.director ? 'dir. ' + row.dataset.director : '';
  var filmSourceParts = [row.dataset.year, director].filter(Boolean);
  metaSource = filmSourceParts.join(' · ');
  metaPersonal = row.dataset.stars || '';
  desc = row.dataset.synopsis || '';
  linkText = '→ View on Letterboxd';
} else if (type === 'music') {
  var musicSourceParts = [row.dataset.artist, row.dataset.album].filter(Boolean);
  metaSource = musicSourceParts.join(' · ');
  metaPersonal = row.dataset.plays ? row.dataset.plays + ' plays' : '';
  desc = row.dataset.bio || '';
  linkText = '→ Listen on Last.fm';
} else if (type === 'article') {
  metaSource = row.dataset.source || '';
  metaPersonal = '';
  desc = row.dataset.description || '';
  linkText = metaSource ? '→ Read on ' + metaSource : '→ Read article';
}

metaSourceEl.textContent = metaSource;

if (metaPersonal) {
  metaPersonalEl.textContent = metaPersonal;
  metaPersonalEl.hidden = false;
} else {
  metaPersonalEl.hidden = true;
}
```

Also find and remove the old:
```javascript
metaEl.textContent = meta;
```

**Step 5: Verify**

Open `index.html`, open a book modal. Should show:
- Title in primary white
- Author in secondary grey
- Stars + finished date in green (books accent)
- Description in tertiary grey

Open a film modal: year + director in grey, stars in amber. Open an article: source in grey, no personal line.

**Step 6: Commit**

```bash
git add style.css index.html
git commit -m "feat: split modal meta into source/personal with accent colour hierarchy"
```

---

### Task 8: Modal navigation (← →)

Adds prev/next arrow buttons flanking the index counter, plus keyboard arrow key support.

**Files:**
- Modify: `style.css` (nav group + button styles)
- Modify: `index.html` (modal HTML + JS)

**Step 1: Add CSS**

In `style.css`, after the `.modal-index` rule (around line 1022), add:

```css
.modal-nav {
  display: flex;
  align-items: center;
  gap: var(--space-1);
  flex-shrink: 0;
}

.modal-prev,
.modal-next {
  background: none;
  border: none;
  cursor: pointer;
  color: var(--text-tertiary);
  font-family: var(--font-mono);
  font-size: 0.75rem;
  padding: 0 2px;
  line-height: 1;
  flex-shrink: 0;
}

.modal-prev:hover,
.modal-next:hover { color: var(--text-primary); }

.modal-prev:disabled,
.modal-next:disabled {
  opacity: 0.3;
  cursor: default;
}

.modal-prev:focus-visible,
.modal-next:focus-visible {
  outline: 1px solid var(--accent);
  outline-offset: 2px;
}
```

**Step 2: Re-inline CSS**

```bash
python3 build.py
```

**Step 3: Update modal HTML**

In `index.html`, in the modal header (after close button was moved to last in Task 5), find:

```html
<span class="modal-type-label" aria-hidden="true"></span>
<span class="modal-index" aria-hidden="true"></span>
<button class="modal-close" aria-label="Close">[ X ]</button>
```

Replace `<span class="modal-index">` with a nav group:

```html
<span class="modal-type-label" aria-hidden="true"></span>
<div class="modal-nav">
  <button class="modal-prev" aria-label="Previous item">←</button>
  <span class="modal-index" aria-hidden="true"></span>
  <button class="modal-next" aria-label="Next item">→</button>
</div>
<button class="modal-close" aria-label="Close">[ X ]</button>
```

**Step 4: Update modal JS**

In the modal IIFE, add new variable declarations near the top (after existing ones):

```javascript
var prevBtn = overlay.querySelector('.modal-prev');
var nextBtn = overlay.querySelector('.modal-next');
var currentSiblings = [];
```

Update `openModal()` — replace the siblings/index block:

Find:
```javascript
// Item index within its panel (e.g. "02 / 05")
var panelBody = row.closest('.panel-body');
var siblings = panelBody
  ? Array.from(panelBody.querySelectorAll('.panel-row[role="button"]'))
  : [row];
var idx = siblings.indexOf(row) + 1;
indexEl.textContent = idx + ' / ' + siblings.length;
```

Replace with:

```javascript
// Item index within its panel + store siblings for navigation
var panelBody = row.closest('.panel-body');
currentSiblings = panelBody
  ? Array.from(panelBody.querySelectorAll('.panel-row[role="button"]'))
  : [row];
var idx = currentSiblings.indexOf(row);
indexEl.textContent = (idx + 1) + ' / ' + currentSiblings.length;
prevBtn.disabled = idx <= 0;
nextBtn.disabled = idx >= currentSiblings.length - 1;
```

Add prev/next click handlers (after the `closeBtn.addEventListener` line):

```javascript
prevBtn.addEventListener('click', function () {
  var idx = currentSiblings.indexOf(activeRow);
  if (idx > 0) openModal(currentSiblings[idx - 1]);
});

nextBtn.addEventListener('click', function () {
  var idx = currentSiblings.indexOf(activeRow);
  if (idx < currentSiblings.length - 1) openModal(currentSiblings[idx + 1]);
});
```

Update the existing `document` keydown handler to add arrow key support:

Find:
```javascript
document.addEventListener('keydown', function (e) {
  if (!overlay.hidden && e.key === 'Escape') closeModal();
});
```

Replace with:
```javascript
document.addEventListener('keydown', function (e) {
  if (overlay.hidden) return;
  if (e.key === 'Escape') { closeModal(); return; }
  if (e.key === 'ArrowLeft')  { prevBtn.click(); return; }
  if (e.key === 'ArrowRight') { nextBtn.click(); return; }
});
```

**Step 5: Verify**

Open `index.html`, click any panel row. Verify:
- Header shows: `[▓] TYPE   ← 02 / 05 →   [ X ]`
- `←` is disabled (greyed) on the first item
- `→` is disabled on the last item
- Clicking `←` / `→` navigates to the adjacent item within the same panel
- Keyboard `←` / `→` arrows navigate between items
- `Escape` still closes
- Tab cycles through: prev, next, close, link (in DOM order)
- Navigating between items updates title, meta, description, image correctly

**Step 6: Commit**

```bash
git add style.css index.html
git commit -m "feat: add panel-scoped prev/next navigation to detail modal"
```

---

### Task 9: Frontend designer review

Pass the completed changes to the frontend designer agent for a visual and UX review pass.

**Prompt:** "Please review the iteration 11 changes in `index.html` and `style.css` for visual consistency with the Y2K / PS2 Memory Card aesthetic. Focus on: (1) warm-up animation timing and feel, (2) modal header layout with type label / nav / close, (3) meta hierarchy colour contrast, (4) nav button sizing and disabled states. Suggest any refinements."

Incorporate feedback before final commit.

---

### Task 10: Final build + push

**Step 1: Pull latest main (Actions bot commits frequently)**

```bash
git restore og-image.png sitemap.xml
git pull --rebase origin main
```

If rebase conflict on `<!-- updated:start/end -->`: keep our HTML structure, take the bot's (newer) timestamp text.

**Step 2: Final build**

```bash
python3 build.py
```

**Step 3: Push to staging for preview**

```bash
git push origin main:staging
```

Wait for CI to pass, then review at the staging URL.

**Step 4: Open PR to main**

```bash
/tmp/gh/gh pr create --title "feat: iteration 11 — visual polish & modal improvements" --body "$(cat <<'EOF'
## Summary
- Warm-up animation: blur/brightness ease-out on `<main>` after boot (~3s)
- Modal: close button moved to top-right
- Modal: widened to 560px, full synopsis (no line-clamp)
- Modal: meta hierarchy — source data grey, personal data in panel accent colour
- Modal: prev/next navigation with keyboard arrow support
- Music panel: added → Last.fm profile footer link

## Test plan
- [ ] Boot sequence plays, then warm-up animation eases in cleanly
- [ ] `prefers-reduced-motion`: no warm-up animation
- [ ] Modal opens on click/Enter for all 4 panel types
- [ ] Close button is top-right; Escape closes modal
- [ ] Modal is 560px wide; descriptions show in full
- [ ] Meta hierarchy: two lines, correct colours per panel type
- [ ] ← → navigation works within panel; disabled at boundaries
- [ ] Keyboard ← → arrows navigate between items
- [ ] Music panel has → Last.fm footer link
- [ ] All four panels bottom-align correctly

🤖 Generated with [Claude Code](https://claude.com/claude-code)
EOF
)"
```

**Step 5: Merge and update docs**

After PR is approved and merged, update:
- `docs/roadmap.md` — mark iteration 11 ✅
- `MEMORY.md` — update Design section with new modal structure details
