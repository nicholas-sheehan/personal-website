# Batch C — CSS Linting Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add Stylelint v16+ to CI as a CSS quality gate, fix the html5validator double-install inefficiency, and add caching for both tools in the deploy job.

**Architecture:** `.stylelintrc.json` (repo root, one rule) is copied into the `_site/` artifact so the deploy job can find it. `html5validator` moves from `requirements.txt` into a new `requirements-ci.txt`; both pip and npm installs in the deploy job are cached. Stylelint is invoked via `./node_modules/.bin/stylelint` to fail explicitly if the install is absent.

**Tech Stack:** Stylelint v16 (npm, no package.json), GitHub Actions (`actions/setup-node@v4` with npm cache, `actions/cache@v4` for pip), html5validator (pip)

**Spec:** `docs/plans/2026-03-15-batch-c-css-linting-design.md`

---

## Chunk 1: Config files and local verification

### Task 1: Add `node_modules/` to `.gitignore`

**Files:**
- Modify: `.gitignore`

- [ ] **Step 1: Add `node_modules/` to `.gitignore`**

Open `.gitignore` and add `node_modules/` after the `# Build output` block:

```
# Build output
_site/
node_modules/
```

- [ ] **Step 2: Commit**

```bash
git add .gitignore
git commit -m "chore: ignore node_modules"
```

---

### Task 2: Create `.stylelintrc.json` and verify locally

**Files:**
- Create: `.stylelintrc.json` (repo root)

- [ ] **Step 1: Create `.stylelintrc.json`**

```json
{
  "rules": {
    "declaration-property-value-no-unknown": true
  }
}
```

- [ ] **Step 2: Install Stylelint locally (no-save — no package.json created)**

```bash
npm install --no-save stylelint@^16
```

Expected: `node_modules/` created at repo root, `node_modules/.bin/stylelint` present. No `package.json` or `package-lock.json` created.

- [ ] **Step 3: Run Stylelint against `style.css` — verify it passes**

```bash
./node_modules/.bin/stylelint style.css
```

Expected: exits 0, no output (clean CSS).

If errors are reported, fix them in `style.css` before proceeding. Each error will show the property, value, and line number.

- [ ] **Step 4: Introduce a deliberate error — verify it fails**

Temporarily add this to the top of `style.css`:

```css
/* TEMP TEST */ body { color: notacolor; }
```

```bash
./node_modules/.bin/stylelint style.css
```

Expected: exits non-zero, output similar to:
```
style.css
  1:20  ✖  Unexpected unknown value "notacolor" for property "color"   declaration-property-value-no-unknown
```

- [ ] **Step 5: Revert the deliberate error**

Remove the `/* TEMP TEST */` line from `style.css`.

```bash
./node_modules/.bin/stylelint style.css
```

Expected: exits 0 again.

- [ ] **Step 6: Commit `.stylelintrc.json`**

```bash
git add .stylelintrc.json
git commit -m "feat: add .stylelintrc.json with declaration-property-value-no-unknown rule"
```

---

### Task 3: Split requirements — move `html5validator` to `requirements-ci.txt`

**Files:**
- Modify: `requirements.txt`
- Create: `requirements-ci.txt`

- [ ] **Step 1: Remove `html5validator` from `requirements.txt`**

`requirements.txt` should read:

```
Pillow>=10,<12
tomli>=2,<3; python_version < "3.11"
```

- [ ] **Step 2: Create `requirements-ci.txt`**

```
html5validator>=0.4,<1
```

- [ ] **Step 3: Verify local pip install works from the new file**

```bash
pip install -r requirements-ci.txt
```

Expected: exits 0. html5validator already installed so output is "Requirement already satisfied".

- [ ] **Step 4: Verify `requirements.txt` still installs cleanly**

```bash
pip install -r requirements.txt
```

Expected: exits 0.

- [ ] **Step 5: Commit**

```bash
git add requirements.txt requirements-ci.txt
git commit -m "feat: split requirements — move html5validator to requirements-ci.txt"
```

---

## Chunk 2: Workflow changes and local validation

### Task 4: Update build job — include new files in artifact

**Files:**
- Modify: `.github/workflows/build.yml` (the "Assemble site files" step in the `build` job)

The current line is:
```yaml
cp index.html og-image.png sitemap.xml favicon.png favicon-192.png favicon.ico robots.txt _site/
```

- [ ] **Step 1: Add `style.css`, `.stylelintrc.json`, and `requirements-ci.txt` to the `cp` command**

Replace the `cp` line with:

```yaml
cp index.html og-image.png sitemap.xml favicon.png favicon-192.png favicon.ico robots.txt style.css .stylelintrc.json requirements-ci.txt _site/
```

---

### Task 5: Update deploy job — replace bare pip install with cached installs for both tools

**Files:**
- Modify: `.github/workflows/build.yml` (the `deploy` job)

The current deploy job starts with:
```yaml
- name: Download site artifact
  uses: actions/download-artifact@v4
  with:
    name: site-${{ github.run_id }}
    path: _site/

- name: Install html5validator
  run: pip install html5validator
```

- [ ] **Step 1: Replace the deploy job's install steps**

Remove `- name: Install html5validator` and replace with the following four steps, inserted between the artifact download and the "Validate HTML" step:

```yaml
      - name: Cache pip (CI tools)
        uses: actions/cache@v4
        with:
          path: ~/.cache/pip
          key: pip-${{ hashFiles('_site/requirements-ci.txt') }}

      - name: Install html5validator
        run: pip install -r _site/requirements-ci.txt

      - name: Cache npm (Stylelint)
        uses: actions/cache@v4
        with:
          path: ~/.npm
          key: ${{ runner.os }}-stylelint-v16

      - name: Install Stylelint
        run: npm install --no-save stylelint@^16
```

- [ ] **Step 2: Add the CSS lint step after "Validate HTML"**

After the existing `Validate HTML` step, add:

```yaml
      - name: Lint CSS
        run: ./node_modules/.bin/stylelint --config _site/.stylelintrc.json _site/style.css
```

The full deploy job step order should now be:
1. Download site artifact
2. Cache pip (CI tools) ← new
3. Install html5validator ← updated (was bare `pip install html5validator`, now uses `requirements-ci.txt`)
4. Cache npm (Stylelint) ← new
5. Install Stylelint ← new
6. Validate HTML ← existing, unchanged
7. Lint CSS ← new
8. Deploy to Cloudflare Pages ← existing, unchanged
9. Check out repo (main only) ← existing, unchanged
10. Deploy Cloudflare Worker (main only) ← existing, unchanged

---

### Task 6: Local end-to-end validation

Before pushing, simulate what CI will do locally.

- [ ] **Step 1: Run the Python build locally**

```bash
python3 build.py
```

Expected: exits 0. Builds `index.html` from existing content (no API keys needed locally — uses cached/stub values).

- [ ] **Step 2: Assemble `_site/` as the build job does**

```bash
mkdir -p _site
cp index.html og-image.png sitemap.xml favicon.png favicon-192.png favicon.ico robots.txt style.css .stylelintrc.json requirements-ci.txt _site/
```

- [ ] **Step 3: Run html5validator against `_site/`**

```bash
html5validator --root _site/ --log INFO --ignore-re "CSS:"
```

Expected: exits 0.

- [ ] **Step 4: Run Stylelint against `_site/style.css`**

`node_modules/` should still be present from Task 2. If you're in a fresh session, re-run `npm install --no-save stylelint@^16` first.

```bash
./node_modules/.bin/stylelint _site/style.css
```

Expected: exits 0.

- [ ] **Step 5: Restore CI artifacts before committing**

```bash
git restore og-image.png sitemap.xml
```

Do NOT restore `index.html` unless you have no structural HTML changes outside the marker blocks.

- [ ] **Step 6: Commit the workflow changes**

```bash
git add .github/workflows/build.yml
git commit -m "feat: add Stylelint to CI, cache pip and npm in deploy job"
```

---

### Task 7: Update docs and push to staging

- [ ] **Step 1: Run the docs-update skill**

Invoke `docs-update` skill. Update: `docs/roadmap.md` (mark Batch C ✅), `MEMORY.md` (Next up section — remove Batch C, update Gotchas if needed), `docs/architecture.md` if any diagram changes are needed, `README.md` if any new secrets or sources were added (none here).

- [ ] **Step 2: Commit docs**

```bash
git add docs/roadmap.md MEMORY.md
git commit -m "docs: update roadmap and memory after Batch C"
```

- [ ] **Step 3: Restore CI artifacts, then push to staging**

```bash
git restore og-image.png sitemap.xml
git pull --rebase origin main
git push origin staging
```

- [ ] **Step 4: Watch the CI run**

Open the Actions tab on GitHub. Verify:
- Build job passes
- Deploy job: "Cache pip" step shows cache miss on first run (expected), installs html5validator
- Deploy job: "Set up Node" step shows cache miss on first run (expected), npm cache configured
- Deploy job: "Install Stylelint" step installs successfully
- Deploy job: "Validate HTML" passes
- Deploy job: "Lint CSS" passes (exits 0)
- Site deploys to `staging.nicsheehan.pages.dev`

- [ ] **Step 5: Open staging in browser and verify the site looks correct**

`https://staging.nicsheehan.pages.dev`
