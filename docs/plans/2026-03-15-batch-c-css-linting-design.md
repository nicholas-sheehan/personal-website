# Design: Batch C — CSS Linting

**Date:** 2026-03-15
**Status:** Approved

## Summary

Add Stylelint v16+ to CI as a quality gate for `style.css`. Runs in the `deploy` job alongside `html5validator`, blocking deployment on CSS errors. Config is minimal — one rule only. Also fixes a pre-existing inefficiency: `html5validator` is currently installed twice per run (once in build, unused; once in deploy, uncached). This batch splits build and CI dependencies and adds caching for both tools in the deploy job.

## Motivation

`html5validator` (vnu) suppresses all CSS errors via `--ignore-re "CSS:"` because vnu's CSS checker doesn't know modern properties (`inset`, `backdrop-filter`, `dvh`). This leaves CSS validity completely unchecked. Stylelint handles modern CSS correctly and catches real errors without false positives.

## Changes

### `.stylelintrc.json` (new file, repo root)

```json
{
  "rules": {
    "declaration-property-value-no-unknown": true
  }
}
```

Single rule. No extended config, no extra plugins.

### `requirements.txt` — remove `html5validator`

`html5validator` is a CI validation tool, not a build dependency. `build.py` never imports or calls it. Remove it from `requirements.txt` so the build job only installs what it actually uses.

**Before:**
```
Pillow>=10,<12
tomli>=2,<3; python_version < "3.11"
html5validator>=0.4,<1
```

**After:**
```
Pillow>=10,<12
tomli>=2,<3; python_version < "3.11"
```

### `requirements-ci.txt` (new file)

CI-only validation tools, separate from build dependencies:

```
html5validator>=0.4,<1
```

### `.github/workflows/build.yml`

**Build job — "Assemble site files" step:** add `style.css`, `.stylelintrc.json`, and `requirements-ci.txt` to the `cp` command so all three are available to the deploy job via the artifact.

```yaml
cp index.html og-image.png sitemap.xml favicon.png favicon-192.png favicon.ico robots.txt style.css .stylelintrc.json requirements-ci.txt _site/
```

**Deploy job — full step order (showing placement of new steps):**

```yaml
- name: Download site artifact        # existing — _site/ now contains style.css, .stylelintrc.json, requirements-ci.txt
  uses: actions/download-artifact@v4
  with:
    name: site-${{ github.run_id }}
    path: _site/

- name: Cache pip (CI tools)          # NEW — hashFiles works because artifact is already downloaded
  uses: actions/cache@v4
  with:
    path: ~/.cache/pip
    key: pip-${{ hashFiles('_site/requirements-ci.txt') }}

- name: Install html5validator        # replaces bare `pip install html5validator`
  run: pip install -r _site/requirements-ci.txt

- name: Cache npm (Stylelint)         # NEW
  uses: actions/cache@v4
  with:
    path: ~/.npm
    key: ${{ runner.os }}-stylelint-v16

- name: Install Stylelint             # NEW
  run: npm install --no-save stylelint@^16

- name: Validate HTML                 # existing — unchanged
  run: html5validator --root _site/ --log INFO --ignore-re "CSS:"

- name: Lint CSS                      # NEW — uses local install, not npx fallback
  run: ./node_modules/.bin/stylelint --config _site/.stylelintrc.json _site/style.css
```

`./node_modules/.bin/stylelint` is used instead of `npx stylelint` to ensure the step fails explicitly if `npm install` did not produce a local install. `npx` would fall back to a fresh download, masking install failures.

`--config _site/.stylelintrc.json` is passed explicitly because `actions/upload-artifact@v4` excludes dotfiles by default. Without this flag, Stylelint's config discovery (cosmiconfig, walking upward from the linted file's directory) cannot find `.stylelintrc.json` in the deploy job since the file is never present in `_site/`. The explicit `--config` flag bypasses discovery entirely.

Both the `npm install` step and the lint step run in the default GitHub Actions working directory (the runner workspace root, e.g. `/home/runner/work/personal-website/personal-website`). No `working-directory:` override is needed or applied. `npm install --no-save` installs into `./node_modules/` at that root, and `./node_modules/.bin/stylelint` resolves from the same location.

Step ordering matters: the artifact download must precede the pip cache step so `_site/requirements-ci.txt` exists when `hashFiles` evaluates it.

## What is NOT changing

- Build job pip caching (via `actions/setup-python` with `cache: 'pip'`) — unchanged
- `html5validator` validate step — unchanged
- No additional Stylelint rules or extended configs
- No `package.json` or lockfile committed to the repo

## Caching strategy

| Tool | Cache path | Key strategy |
|------|-----------|--------------|
| pip (deploy) | `~/.cache/pip` | `hashFiles('_site/requirements-ci.txt')` — busts automatically on version bump |
| npm (Stylelint) | `~/.npm` | `actions/cache@v4` with key `${{ runner.os }}-stylelint-v16` — includes OS in key for correctness; bump `v16` manually when upgrading Stylelint. `~/.npm` is npm's tarball download cache; on cache hit `npm install` skips network downloads and writes `./node_modules/` from local tarballs. `actions/setup-node` with `cache: 'npm'` was considered but requires a lockfile or `package.json`; explicit `actions/cache` is used instead to avoid that dependency. |

This mirrors the pattern already used in the build job (`actions/setup-python` with `cache: 'pip'` keyed off `requirements.txt`).

## Dependency split rationale

| File | Purpose | Used by |
|------|---------|---------|
| `requirements.txt` | Build dependencies (Pillow, tomli) | Build job only |
| `requirements-ci.txt` | CI validation tools (html5validator) | Deploy job only |

Before this change, `html5validator` was installed in the build job (via `requirements.txt`, cached but unused) and again in the deploy job (direct `pip install`, uncached). It was hitting the network on every deploy.

## Success criteria

- Build job no longer installs `html5validator` (it's not in `requirements.txt`)
- Deploy job installs `html5validator` from `_site/requirements-ci.txt` with pip caching
- Deploy job installs Stylelint with npm caching
- `.stylelintrc.json` is present in `_site/` alongside `style.css` (config discovery walks upward from the linted file)
- `./node_modules/.bin/stylelint _site/style.css` exits 0 in CI with the current `style.css`
- A deliberate invalid declaration (e.g. `color: notacolor`) causes the CSS lint step to fail
- If `npm install` fails, the lint step also fails (does not fall back to npx download)
- Deploy is blocked when either HTML validation or CSS lint fails
