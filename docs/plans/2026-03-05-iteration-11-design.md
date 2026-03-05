# Iteration 11 Design — Visual Polish & Modal Improvements

Date: 2026-03-05

## Scope

Pure frontend — no new infrastructure, no `build.py` changes. Six improvements that make the site feel more considered.

## 1. Warm-up animation

After the boot overlay fades, a CSS filter animation runs on `<main>` giving a "screen dialling in" effect.

**Approach:** CSS `filter: blur + brightness`, applied via a `.warming-up` class added by the boot JS. Duration 3s, ease-out.

```css
@keyframes warmup {
  0%   { filter: blur(4px) brightness(0.4); }
  60%  { filter: blur(1px) brightness(0.9); }
  100% { filter: blur(0)   brightness(1);   }
}
.warming-up {
  animation: warmup 3s ease-out forwards;
}
```

**JS change (boot sequence):** In the `fadeOut()` callback, after revealing `<main>`:
1. Clear `mn.style.animation = ""` (the inline `"none"` set at boot start would otherwise block the class animation)
2. Add `mn.classList.add("warming-up")`

Reduced-motion users: skip — do not add the class.

**Stacking context note:** The boot overlay and modal are siblings of `<main>` (not children), so `filter` on `<main>` does not affect their `position: fixed` behaviour.

## 2. Modal close button — move to top-right

The `<button class="modal-close">` is currently the first child of `.modal-header` (left side). Move it to last child so it sits on the far right.

New DOM order in `.modal-header`:
1. `span.modal-type-label` (flex: 1 — expands, left-anchored)
2. `div.modal-nav` (← index →, see §5)
3. `button.modal-close` (far right)

Resulting layout:
```
[▓] BOOKS         ← 02 / 05 →  [ X ]
```

## 3. Modal size + synopsis

- `max-width`: `400px` → `560px`
- Remove the `-webkit-line-clamp: 4` block from `.modal-desc` (descriptions are already capped at ~400 chars by `build.py`)

## 4. Modal meta hierarchy

Split the single `.modal-meta` paragraph into two separate elements:

| Element | Content | Style |
|---|---|---|
| `.modal-meta-source` | author / year + director / artist + album / domain | `--text-secondary` |
| `.modal-meta-personal` | stars + finished date / stars / play count | `--modal-accent` (panel colour) |

Per content type:

- **Books:** source = `author`, personal = `stars · Finished Month Year`
- **Films:** source = `year · dir. Director`, personal = `stars`
- **Music:** source = `artist · album`, personal = `N plays`
- **Articles:** source = `domain`, personal = none (`.modal-meta-personal` hidden)

HTML change: replace `<p class="modal-meta">` with two `<p>` elements.
JS change: `openModal()` populates both elements separately.
CSS: two new rules replacing `.modal-meta`.

## 5. Modal navigation (← →)

Replace `<span class="modal-index">` with a `<div class="modal-nav">` group:

```html
<div class="modal-nav">
  <button class="modal-prev" aria-label="Previous item">←</button>
  <span class="modal-index" aria-hidden="true"></span>
  <button class="modal-next" aria-label="Next item">→</button>
</div>
```

**Behaviour:**
- Siblings scoped to `.panel-body` (same logic as existing index calculation)
- Prev/Next buttons `disabled` at panel boundaries
- Keyboard: `ArrowLeft` / `ArrowRight` trigger the buttons while modal is open (added to the existing `document` keydown handler)
- Focus stays within modal; arrows do not conflict with tab trap

**CSS:** `.modal-nav` is a flex row with small gap; `.modal-prev` / `.modal-next` styled like `.modal-close` (monospace, tertiary colour, no border); `disabled` state at 30% opacity.

## 6. Last.fm footer link

Add a static `<footer class="panel-footer">` to the music panel in `index.html`, after the `<!-- music:end -->` marker and its closing `</div>`, before `</section>`. This mirrors the Books (→ Goodreads) and Films (→ Letterboxd) panels and resolves the bottom panel height mismatch.

```html
<!-- music:end -->
              </div>
              <footer class="panel-footer">
                <a href="https://www.last.fm/user/tonic-lastfm" class="panel-footer-link"
                   target="_blank" rel="noopener noreferrer">→ Last.fm</a>
              </footer>
            </section>
```

Outside the markers — survives CI rebuilds.

## Files changed

| File | Changes |
|---|---|
| `style.css` | Warm-up keyframes + `.warming-up`; `.modal-box` max-width; `.modal-desc` remove line-clamp; `.modal-meta-source` / `.modal-meta-personal`; `.modal-nav` / `.modal-prev` / `.modal-next` |
| `index.html` | Boot JS (warm-up trigger); modal HTML (header reorder, nav group, meta split); modal JS (`openModal()`, prev/next handlers, arrow keys); music panel static footer |

No `build.py` changes.

## Workflow note

Pass this plan to the frontend designer agent for review before implementation.
