# Iteration 7 — Favicon & OG Image Redesign Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Bring the favicon and OG image in line with the Y2K aesthetic — dark `#050a14` background, JetBrains Mono font, `#3b82f6` accent.

**Architecture:** Bundle JetBrains Mono TTF files under `assets/` (committed to repo). Update `generate_og_image()` in `build.py` in-place. Add a new `cmd_favicons()` command (run once, generates static favicon files that are committed to the repo — not run on every build).

**Tech Stack:** Python 3.9+, Pillow (already a dependency), JetBrains Mono TTF (bundled).

---

## Before Starting

No worktree needed — all changes are self-contained and low-risk.

---

### Task 1: Bundle JetBrains Mono font files

**Files:**
- Create: `assets/JetBrainsMono-Regular.ttf`
- Create: `assets/JetBrainsMono-Bold.ttf`

**Step 1: Create the assets directory and download the fonts**

```bash
mkdir -p assets
curl -L "https://github.com/JetBrains/JetBrainsMono/raw/master/fonts/ttf/JetBrainsMono-Regular.ttf" \
  -o assets/JetBrainsMono-Regular.ttf
curl -L "https://github.com/JetBrains/JetBrainsMono/raw/master/fonts/ttf/JetBrainsMono-Bold.ttf" \
  -o assets/JetBrainsMono-Bold.ttf
```

**Step 2: Verify the files exist and are non-empty**

```bash
python3 -c "
import os
for f in ['assets/JetBrainsMono-Regular.ttf', 'assets/JetBrainsMono-Bold.ttf']:
    size = os.path.getsize(f)
    print(f'{f}: {size:,} bytes')
    assert size > 100_000, f'{f} looks too small — download may have failed'
print('Fonts OK')
"
```

Expected: both files are ~250–500KB. If either is tiny (a few hundred bytes), the download failed — check the URL and retry.

**Step 3: Verify Pillow can load them**

```bash
python3 -c "
from PIL import ImageFont
r = ImageFont.truetype('assets/JetBrainsMono-Regular.ttf', 24)
b = ImageFont.truetype('assets/JetBrainsMono-Bold.ttf', 24)
print('Regular:', r)
print('Bold:', b)
"
```

Expected: no errors, prints font object representations.

**Step 4: Commit**

```bash
git add assets/
git commit -m "feat: bundle JetBrains Mono TTF for OG image and favicon generation"
```

---

### Task 2: Update `generate_og_image()` in `build.py`

**Files:**
- Modify: `build.py` — replace `generate_og_image()` (lines ~329–413)

**Step 1: Replace the function**

Find the existing `generate_og_image()` function in `build.py` and replace it entirely with:

```python
def generate_og_image(profile: dict, output_path: str):
    """Generate a 1200x630 OG image with avatar, name, and tagline."""
    try:
        from PIL import Image, ImageDraw, ImageFont
        import io
    except ImportError:
        print("  ⚠  Pillow not installed — skipping OG image generation.")
        return False

    WIDTH, HEIGHT = 1200, 630
    BG_COLOR = (5, 10, 20)            # #050a14
    TEXT_PRIMARY = (226, 232, 240)    # #e2e8f0
    TEXT_SECONDARY = (100, 116, 139)  # #64748b
    ACCENT = (59, 130, 246)           # #3b82f6

    img = Image.new("RGB", (WIDTH, HEIGHT), BG_COLOR)
    draw = ImageDraw.Draw(img)

    # Borders — 2px top, 4px left (panel accent)
    draw.rectangle([(0, 0), (WIDTH, 1)], fill=ACCENT)
    draw.rectangle([(0, 0), (3, HEIGHT)], fill=ACCENT)

    # Load fonts — assets/ first, fall back to system mono
    def load_font(size, bold=False):
        weight = "Bold" if bold else "Regular"
        asset = os.path.join("assets", f"JetBrainsMono-{weight}.ttf")
        fallbacks = [
            "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf" if bold
            else "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
            "/System/Library/Fonts/Courier.ttc",
        ]
        if os.path.exists(asset):
            try:
                return ImageFont.truetype(asset, size)
            except (OSError, IOError):
                pass
        for p in fallbacks:
            try:
                return ImageFont.truetype(p, size)
            except (OSError, IOError):
                continue
        return ImageFont.load_default()

    font_name = load_font(54, bold=True)
    font_tagline = load_font(24)
    font_url = load_font(20)

    # Download and composite avatar
    avatar_url = profile.get("avatar_url", "")
    avatar_size = 180
    avatar_x, avatar_y = 100, (HEIGHT - avatar_size) // 2

    if avatar_url:
        try:
            req = urllib.request.Request(f"{avatar_url}?s=400",
                                         headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=15) as resp:
                avatar_data = resp.read()
            avatar = Image.open(io.BytesIO(avatar_data)).resize(
                (avatar_size, avatar_size), Image.LANCZOS
            )
            # Circular mask
            mask = Image.new("L", (avatar_size, avatar_size), 0)
            mask_draw = ImageDraw.Draw(mask)
            mask_draw.ellipse((0, 0, avatar_size, avatar_size), fill=255)
            # Blue ring
            ring_pad = 4
            ring_r = avatar_size // 2 + ring_pad
            cx = avatar_x + avatar_size // 2
            cy = avatar_y + avatar_size // 2
            draw.ellipse(
                (cx - ring_r, cy - ring_r, cx + ring_r, cy + ring_r),
                outline=ACCENT, width=3,
            )
            img.paste(avatar, (avatar_x, avatar_y), mask)
        except Exception as e:
            print(f"  ⚠  Could not download avatar: {e}")

    # Name and tagline
    text_x = avatar_x + avatar_size + 60
    name = profile.get("display_name", "")
    tagline = build_gravatar_tagline(profile)

    name_y = HEIGHT // 2 - 45
    draw.text((text_x, name_y), name, fill=TEXT_PRIMARY, font=font_name)

    if tagline:
        draw.text((text_x, name_y + 72), tagline, fill=TEXT_SECONDARY, font=font_tagline)

    # URL label — bottom right
    url_text = "nicsheehan.com"
    bbox = draw.textbbox((0, 0), url_text, font=font_url)
    url_w = bbox[2] - bbox[0]
    draw.text((WIDTH - url_w - 60, HEIGHT - 56), url_text, fill=ACCENT, font=font_url)

    img.save(output_path, "PNG", optimize=True)
    return True
```

**Step 2: Verify the function runs without errors (no credentials needed for this test)**

```bash
python3 -c "
import build
# Test with a minimal profile dict (no avatar — skips the network call)
profile = {'display_name': 'Nicholas Sheehan', 'job_title': 'Web Developer', 'company': 'Test'}
result = build.generate_og_image(profile, '/tmp/test-og.png')
print('Generated:', result)

from PIL import Image
img = Image.open('/tmp/test-og.png')
print('Size:', img.size)   # expect (1200, 630)
print('Mode:', img.mode)   # expect RGB

# Check top-left pixel is the accent colour (border)
px = img.getpixel((0, 0))
print('Top-left pixel:', px)   # expect (59, 130, 246)

# Check centre-ish pixel is background
px2 = img.getpixel((600, 315))
print('Centre pixel:', px2)   # expect close to (5, 10, 20)
"
```

Expected: `Generated: True`, size `(1200, 630)`, top-left pixel `(59, 130, 246)` (accent border), centre pixel dark.

**Step 3: Commit**

```bash
git add build.py
git commit -m "feat: update generate_og_image() with Y2K aesthetic"
```

---

### Task 3: Add `cmd_favicons()` and update `main()`

**Files:**
- Modify: `build.py` — add `cmd_favicons()` function + constants, update `main()`

**Step 1: Add favicon constants near the top of `build.py`**

Find the block where `OG_IMAGE_PATH` is defined (around line 96) and add:

```python
FAVICON_ICO_PATH = "favicon.ico"
FAVICON_PNG_PATH = "favicon.png"
FAVICON_192_PATH = "favicon-192.png"
ASSETS_DIR = "assets"
```

**Step 2: Add the helper and command functions**

Add both functions to `build.py` immediately before the `main()` function (around line 922):

```python
def _draw_favicon(size: int) -> "Image.Image":
    """Render a single favicon image at the given square pixel size."""
    from PIL import Image, ImageDraw, ImageFont
    BG = (5, 10, 20)        # #050a14
    ACCENT = (59, 130, 246)  # #3b82f6

    img = Image.new("RGB", (size, size), BG)
    draw = ImageDraw.Draw(img)

    font_path = os.path.join(ASSETS_DIR, "JetBrainsMono-Bold.ttf")
    font_size = int(size * 0.65)
    try:
        font = ImageFont.truetype(font_path, font_size)
    except (OSError, IOError):
        font = ImageFont.load_default()

    # Centre "N" precisely
    bbox = draw.textbbox((0, 0), "N", font=font)
    w = bbox[2] - bbox[0]
    h = bbox[3] - bbox[1]
    x = (size - w) // 2 - bbox[0]
    y = (size - h) // 2 - bbox[1]
    draw.text((x, y), "N", fill=ACCENT, font=font)

    return img


def cmd_favicons():
    """Generate favicon.png (48px), favicon-192.png, and favicon.ico (multi-res)."""
    try:
        from PIL import Image
    except ImportError:
        print("⚠  Pillow not installed — run: pip install Pillow")
        return

    font_path = os.path.join(ASSETS_DIR, "JetBrainsMono-Bold.ttf")
    if not os.path.exists(font_path):
        print(f"⚠  Font not found at {font_path} — run Task 1 first.")
        return

    print("Generating favicons…")

    img_192 = _draw_favicon(192)
    img_192.save(FAVICON_192_PATH, "PNG", optimize=True)
    print(f"  Saved {FAVICON_192_PATH}")

    img_48 = _draw_favicon(48)
    img_48.save(FAVICON_PNG_PATH, "PNG", optimize=True)
    print(f"  Saved {FAVICON_PNG_PATH}")

    # Multi-res ICO: Pillow scales from the 48px source to 16, 32, 48
    img_48.save(FAVICON_ICO_PATH, format="ICO", sizes=[(16, 16), (32, 32), (48, 48)])
    print(f"  Saved {FAVICON_ICO_PATH}")

    print("Favicons generated ✓")
```

**Step 3: Update `main()` to dispatch the new command**

Find and replace the existing `main()` function:

```python
def main():
    if len(sys.argv) > 1 and sys.argv[1] == "auth":
        cmd_auth()
    elif len(sys.argv) > 1 and sys.argv[1] == "favicons":
        cmd_favicons()
    else:
        cmd_build()
```

**Step 4: Verify `cmd_favicons` is importable and callable without errors**

```bash
python3 -c "
import build
print('cmd_favicons:', build.cmd_favicons)
print('_draw_favicon:', build._draw_favicon)
print('FAVICON_ICO_PATH:', build.FAVICON_ICO_PATH)
"
```

Expected: all three print without ImportError or AttributeError.

**Step 5: Commit**

```bash
git add build.py
git commit -m "feat: add cmd_favicons() command to build.py"
```

---

### Task 4: Generate favicons and commit static files

**Files:**
- Modify: `favicon.png`, `favicon-192.png`, `favicon.ico`

**Step 1: Run the favicon generator**

```bash
python3 build.py favicons
```

Expected output:
```
Generating favicons…
  Saved favicon-192.png
  Saved favicon.png
  Saved favicon.ico
Favicons generated ✓
```

**Step 2: Verify dimensions and content**

```bash
python3 -c "
from PIL import Image

for path, expected_size in [
    ('favicon.png', (48, 48)),
    ('favicon-192.png', (192, 192)),
]:
    img = Image.open(path)
    assert img.size == expected_size, f'{path}: expected {expected_size}, got {img.size}'
    # Check background colour at a corner
    px = img.getpixel((2, 2))
    print(f'{path}: size={img.size}, corner pixel={px}')

# Check ICO exists and is non-empty
import os
size = os.path.getsize('favicon.ico')
print(f'favicon.ico: {size:,} bytes')
assert size > 1000, 'favicon.ico looks too small'

print('All checks passed')
"
```

Expected: both PNGs at correct sizes, `favicon.ico` > 1KB.

**Step 3: Open the 192px version and visually inspect it**

```bash
open favicon-192.png
```

Check: dark background, blue "N" centred, clearly legible.

**Step 4: Commit the generated files**

```bash
git add favicon.png favicon-192.png favicon.ico
git commit -m "feat: regenerate favicons with Y2K design (dark bg, mono N)"
```

---

### Task 5: Run full build and verify OG image

**Step 1: Run the full build with credentials**

```bash
GRAVATAR_API_KEY="..." \
INSTAPAPER_CONSUMER_KEY="..." \
INSTAPAPER_CONSUMER_SECRET="..." \
INSTAPAPER_OAUTH_TOKEN="..." \
INSTAPAPER_OAUTH_TOKEN_SECRET="..." \
LASTFM_API_KEY="..." \
python3 build.py
```

Expected: build completes with `Saved og-image.png` printed.

**Step 2: Verify OG image**

```bash
python3 -c "
from PIL import Image
img = Image.open('og-image.png')
print('Size:', img.size)          # expect (1200, 630)
# Top border: pixel at (100, 0) should be accent blue
px = img.getpixel((100, 0))
print('Top border pixel:', px)    # expect (59, 130, 246)
# Left border: pixel at (0, 300) should be accent blue
px2 = img.getpixel((0, 300))
print('Left border pixel:', px2)  # expect (59, 130, 246)
print('OG image OK')
"
```

**Step 3: Open and visually inspect**

```bash
open og-image.png
```

Check:
- Dark `#050a14` background
- Blue top + left border
- Avatar with blue ring on the left
- Name in mono bold, tagline below in lighter mono
- `nicsheehan.com` bottom-right in blue

**Step 4: Restore build artifacts and commit if needed**

The OG image is a CI artifact — don't commit the locally-generated version:

```bash
git restore og-image.png sitemap.xml index.html
```

---

### Task 6: Update roadmap

**Files:**
- Modify: `docs/roadmap.md`

**Step 1: Mark iteration 7 as shipped**

In `docs/roadmap.md`, find the iteration 7 section and update:

```markdown
## Iteration 7 — Favicon & OG image redesign ✅ shipped 2026-02-22
Visual identity refresh — bring favicon and OG image in line with the Y2K aesthetic.

- [x] Favicon redesign — dark `#050a14` background, accent-blue "N" in JetBrains Mono Bold; `favicon.png` (48px), `favicon-192.png`, `favicon.ico` (multi-res)
- [x] OG image redesign — Y2K palette (`#050a14`), top+left accent border, JetBrains Mono font, `nicsheehan.com` label bottom-right; avatar layout unchanged
- [x] Bundle JetBrains Mono TTF under `assets/` for Pillow use
- [x] New `python3 build.py favicons` command for one-time favicon generation
```

**Step 2: Commit**

```bash
git add docs/roadmap.md
git commit -m "docs: mark iteration 7 complete in roadmap"
```

---

### Final: push

```bash
git restore og-image.png sitemap.xml index.html
git pull --rebase origin main
git push origin main
```
