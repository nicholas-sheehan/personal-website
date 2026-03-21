# Development Pipeline

## Branch strategy

| Branch | Purpose | Deploys to |
|--------|---------|------------|
| `main` | Production — what is live | www.nicsheehan.com (Cloudflare Pages) |
| `staging` | Pre-production — full build with real data | staging.nicsheehan.pages.dev (Cloudflare Pages preview) |
| Feature branches | Active development — one per iteration | Local preview only |

**Never push directly to `main`.** All changes flow through a pull request. The build bot pushes feed updates directly as part of CI via a dedicated deploy key (`BOT_DEPLOY_KEY`) — this is the only exception. Bot commits use `[skip ci]` to prevent retriggering the workflow.

## How changes move to production

```mermaid
flowchart TD
    FB[Feature branch] --> LP[Local preview\nRun build without API keys\nExisting feed content preserved]
    LP -->|approved| STG[Push to staging branch]
    STG --> CI1[CI: full build\nReal API data via GitHub secrets]
    CI1 --> SR[Staging review\nOpen staging.nicsheehan.pages.dev]
    SR -->|approved| PR[Pull request: staging → main]
    PR --> CI2[CI: build + deploy\nto Cloudflare Pages]
    CI2 --> PROD[Production\nwww.nicsheehan.com]

    LP -->|needs fixes| FB
    SR -->|needs fixes| FB
```

## Stage 1 — Local preview

Run `python3 build.py` without API keys. The build re-inlines CSS and updates timestamps but preserves existing feed content between markers. Open `index.html` in your browser. Then validate the HTML:

```bash
mkdir -p _site && cp index.html _site/ && html5validator --root _site/ --log INFO --ignore-re "CSS:"
```

**Nothing should break in the staging → main PR.** Every check that runs in CI must pass locally before pushing to staging. Staging is for verifying real API data — not for discovering broken HTML or build errors.

**Use for:** CSS changes, HTML structure, JavaScript behaviour, design work.

## Stage 2 — Staging review

Push to the `staging` branch. GitHub Actions runs a full build using real API secrets, commits the result back to `staging`, and deploys to Cloudflare Pages. Open the staging preview URL in your browser.

**Use for:** data pipeline changes, new API fields, new content sources.

Push to the `staging` branch and open `staging.nicsheehan.pages.dev` in your browser once CI completes.

## Stage 3 — Production

Open a pull request from `staging` to `main`. Review the diff. **Merge using a merge commit (not squash).** GitHub Actions builds and deploys to Cloudflare Pages automatically.

**Why merge commit, not squash:** `staging` is a long-lived branch. Squash merge creates a new SHA on `main` that git has never seen on `staging`, so the next `git pull --rebase origin main` tries to replay all staging commits as if they were new — causing conflicts with themselves. Merge commit preserves the exact SHAs, so the next sync is a no-op.

## CI behaviour by branch

| Branch | Build job | Deploy job |
|--------|-----------|------------|
| `main` | ✅ runs | ✅ runs → www.nicsheehan.com + Worker auto-deploy |
| `staging` | ✅ runs | ✅ runs → staging.nicsheehan.pages.dev |
| Feature branches | ❌ not triggered | ❌ not triggered |

**CI internals:** Concurrent runs on the same branch are cancelled (concurrency key on `github.ref`). Built `_site/` is passed from the build job to the deploy job via GitHub artifact (no `git pull` race). HTML is validated with `html5validator` and CSS is linted with Stylelint (`declaration-property-value-no-unknown`) before deploy — both steps are blocking. Bot commit is skipped when only the `<!-- updated -->` timestamp changed.

**Commit signing:** All personal commits (via 1Password SSH agent, `id_ed25519_github` key) and bot commits (GPG key via `BOT_GPG_KEY` secret) are signed. Signed commits show "Verified" on GitHub. **Push detector:** `.github/workflows/push-detector.yml` triggers on every push to `main`; opens a GitHub Issue if the commit's git author is not `github-actions[bot]` and the message doesn't start with "Merge pull request" — catching any direct human push that bypasses the PR requirement.
