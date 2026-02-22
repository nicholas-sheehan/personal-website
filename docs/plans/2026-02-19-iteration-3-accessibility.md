# Iteration 3 — Accessibility & Contrast Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Fix light mode contrast failures and add keyboard accessibility improvements before the upcoming layout overhaul.

**Architecture:** Two CSS-only changes in `style.css` (tertiary color + avatar border) and one structural HTML change in `index.html` (skip-to-content link). The CSS changes propagate to `index.html` automatically at the next build since `style.css` is inlined between `<!-- style:start/end -->` markers. For the skip link, the `<body>` and `<main>` tags are static HTML outside any build markers, so the structural change is made directly in `index.html`.

**Tech Stack:** CSS custom properties, WCAG 2.1 AA contrast (4.5:1 minimum for normal text)

---

### Task 1: Fix light mode contrast — shift tertiary text to a passing cool gray

**Files:**
- Modify: `style.css:362–377` (light mode `:root` block)

**Background:**

Current light mode tertiary: `#a8a29e` (warm stone) on `--bg: #fafafa` = ~2.9:1 contrast. WCAG AA requires 4.5:1 for normal-sized text. The tertiary color is used for `h2` section headings, `.source` mono spans, and `.colophon` text.

The fix: replace the warm stone color with a cool blue-gray that passes 4.5:1. Also clean up the `.colophon .credits` override which is currently `#c4b5a4` (an even lighter warm tan, also failing).

**Chosen replacement:** `#5f6b7a`
- rgb(95, 107, 122) — a genuine cool blue-gray, not warm
- Contrast with `#fafafa`: ~5.1:1 ✓ (passes AA)
- Sits visibly lighter than `--text-secondary: #57534e` (6.9:1) — hierarchy preserved

**Step 1: Read `style.css` lines 358–380 to confirm current values**

**Step 2: Update `--text-tertiary` in the light mode block**

In `style.css`, find the light mode block:
```css
@media (prefers-color-scheme: light) {
  :root {
    --bg: #fafafa;
    --text-primary: #1c1917;
    --text-secondary: #57534e;
    --text-tertiary: #a8a29e;
    --accent: #3b82f6;
    --accent-hover: #2563eb;
    --border: #e5e5e5;
    --surface: #f5f5f4;
  }

  .colophon .credits {
    color: #c4b5a4;
  }
}
```

Replace with:
```css
@media (prefers-color-scheme: light) {
  :root {
    --bg: #fafafa;
    --text-primary: #1c1917;
    --text-secondary: #57534e;
    --text-tertiary: #5f6b7a;
    --accent: #3b82f6;
    --accent-hover: #2563eb;
    --border: #e5e5e5;
    --surface: #f5f5f4;
  }

  .colophon .credits {
    color: var(--text-tertiary);
  }
}
```

Two changes:
- `--text-tertiary`: `#a8a29e` → `#5f6b7a`
- `.colophon .credits`: hardcoded `#c4b5a4` → `var(--text-tertiary)` (now uses the token, removes a second failing hardcode)

**Step 3: Verify contrast ratios with a quick script**

```bash
python3 -c "
def luminance(hex_color):
    hex_color = hex_color.lstrip('#')
    r, g, b = (int(hex_color[i:i+2], 16) / 255 for i in (0, 2, 4))
    def chan(c):
        return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4
    return 0.2126 * chan(r) + 0.7152 * chan(g) + 0.0722 * chan(b)

def contrast(a, b):
    la, lb = luminance(a), luminance(b)
    lighter, darker = max(la, lb), min(la, lb)
    return (lighter + 0.05) / (darker + 0.05)

bg = '#fafafa'
old = '#a8a29e'
new = '#5f6b7a'
sec = '#57534e'
print(f'Old tertiary ({old}) on {bg}: {contrast(old, bg):.2f}:1')
print(f'New tertiary ({new}) on {bg}: {contrast(new, bg):.2f}:1  (need >= 4.5)')
print(f'Secondary   ({sec}) on {bg}: {contrast(sec, bg):.2f}:1')
assert contrast(new, bg) >= 4.5, f'FAIL: {contrast(new, bg):.2f}:1'
assert contrast(new, bg) < contrast(sec, bg), 'Hierarchy broken: tertiary must be lighter than secondary'
print('OK — passes AA, hierarchy preserved')
"
```
Expected: old ~2.9:1, new ~5.1:1, OK message.

**Step 4: Commit**
```bash
git add style.css
git commit -m "Fix light mode tertiary contrast — #a8a29e → #5f6b7a (2.9:1 → 5.1:1)"
```

---

### Task 2: Add skip-to-content link for keyboard accessibility

**Files:**
- Modify: `index.html` — add skip link after `<body>`, add `id` to `<main>`
- Modify: `style.css` — add `.skip-to-content` styles

**Background:** Keyboard users (and screen reader users) tabbing through the page currently have no way to jump past the nav links to the main content. The skip link is the standard fix: visually hidden until focused, then slides into view.

**Step 1: Read `index.html` lines 470–476 to confirm `<body>` and `<main>` structure**

Expected to see:
```html
<body>
  <main>
    <div class="container">
      <header class="hero">
```

**Step 2: Update `index.html` — add skip link and `id` to `<main>`**

Find:
```html
<body>
  <main>
```

Replace with:
```html
<body>
  <a class="skip-to-content" href="#main-content">Skip to main content</a>
  <main id="main-content">
```

**Step 3: Add `.skip-to-content` CSS to `style.css`**

Add this block in `style.css` just after the `/* --- Reset & base --- */` section (after the `body` rule, before `/* --- Layout --- */`):

```css
/* --- Skip to content --- */

.skip-to-content {
  position: absolute;
  top: -100%;
  left: 1rem;
  padding: 0.5rem 1rem;
  background: var(--accent);
  color: #fff;
  font-size: 0.875rem;
  font-weight: 500;
  border-radius: 0 0 4px 4px;
  text-decoration: none;
  z-index: 100;
  transition: top 0.1s ease;
}

.skip-to-content:focus {
  top: 0;
}
```

**Step 4: Verify**

```bash
grep -n "skip-to-content\|main-content" index.html
grep -n "skip-to-content" style.css
```

Expected:
- `index.html`: two hits — the `<a class="skip-to-content">` link and `<main id="main-content">`
- `style.css`: two hits — the selector and `:focus` rule

**Step 5: Commit**

```bash
git add index.html style.css
git commit -m "Add skip-to-content link for keyboard accessibility"
```

---

### Task 3: Soften avatar border — `var(--accent)` → `var(--border)`

**Files:**
- Modify: `style.css:72–77` (`.avatar` rule)

**Background:** The avatar currently has a bright blue `var(--accent)` border (`#3b82f6` in dark, `#3b82f6` in light). The roadmap calls for softening it to `var(--border)` — a subtle `#262626` in dark, `#e5e5e5` in light. The print media query already has `.avatar { border-color: #ccc; }` which can be removed since `var(--border)` in print is already `#ccc`.

**Step 1: Read `style.css` lines 72–77 to confirm the `.avatar` rule**

**Step 2: Update `.avatar` border in `style.css`**

Find:
```css
.avatar {
  border-radius: 50%;
  margin-bottom: 1rem;
  border: 2px solid var(--accent);
  box-shadow: none;
}
```

Replace with:
```css
.avatar {
  border-radius: 50%;
  margin-bottom: 1rem;
  border: 2px solid var(--border);
  box-shadow: none;
}
```

**Step 3: Remove the now-redundant print override**

In the `@media print` block (around line 414), find and remove:
```css
  .avatar {
    border-color: #ccc;
  }
```

This override is no longer needed because `var(--border)` resolves to `#ccc` in the print block's `:root` override.

**Step 4: Verify**

```bash
grep -n "border.*accent\|border.*border" style.css | grep -i avatar
grep -n "avatar" style.css
```

Expected: `.avatar` rule shows `var(--border)`, the print override is gone.

**Step 5: Commit**

```bash
git add style.css
git commit -m "Soften avatar border from accent blue to var(--border)"
```

---

### Final: update the style inline in index.html and push

Since `style.css` is inlined by the build script, the changes won't appear in the live `index.html` until the next CI build. To keep the local `index.html` consistent now, run a local sync of just the style block:

```bash
python3 -c "
import re

style = open('style.css').read()
html = open('index.html').read()
new_style = f'  <style>\n{style}  </style>'
pattern = re.compile(r'(<!-- style:start -->)\n.*?\n(\s*<!-- style:end -->)', re.DOTALL)
result, count = pattern.subn(rf'\1\n{new_style}\n\2', html)
if count:
    open('index.html', 'w').write(result)
    print('Updated index.html style block')
else:
    print('WARNING: style markers not found')
"
```

Then commit and push:
```bash
git add index.html
git commit -m "Sync inlined CSS in index.html"
git pull --rebase origin main
git push origin main
```
