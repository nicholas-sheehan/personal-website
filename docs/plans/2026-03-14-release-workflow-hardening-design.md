# Design: Release Workflow Hardening

**Date:** 2026-03-14
**Status:** Approved

## Goal

Harden the release workflow by setting up SSH authentication, installing `gh` CLI properly, creating a dedicated deploy key for the build bot, and re-enabling branch protection on `main` via a GitHub Ruleset with appropriate bypass actors.

## Background

Branch protection on `main` was removed on 2026-03-02 because the GitHub Actions build bot needs to push feed updates directly to `main`, and protection rules blocked it. The proper fix is a deploy key scoped to the bot with bypass actor status in a Ruleset — convention alone is not a sufficient guard (proven 2026-03-05).

## Sections

### 1. Personal SSH Key

Generate an ED25519 key pair on the local machine (`~/.ssh/id_ed25519`). Add the public key to the GitHub account under Settings → SSH keys. Switch the repo remote from HTTPS to SSH:

```
git remote set-url origin git@github.com:nicholas-sheehan/personal-website.git
```

All future git operations authenticate via key — no credential prompts.

### 2. `gh` CLI Install + Auth

Install via Homebrew (`brew install gh`). Authenticate with `gh auth login` — interactive flow, authenticates against GitHub. Available permanently after install; no more per-session zip downloads.

### 3. Deploy Key for the Build Bot

Generate a second ED25519 key pair dedicated to the bot (separate from the personal key).

- **Private key** → added to the repo as a GitHub Secret (`BOT_DEPLOY_KEY`)
- **Public key** → added to the repo under Settings → Deploy keys with write access

The CI workflow (`build.yml`) is updated to use this key when pushing the build output back to `main`.

### 4. GitHub Ruleset on `main`

Create a Ruleset on `main` with the following configuration:

- **Enforcement:** Active
- **Target branch:** `main`
- **Rules:** Require a pull request before merging; block direct pushes
- **Bypass actors:**
  - Repository administrators (owner bypass — requires deliberate action, logged in audit trail)
  - The deploy key (allows build bot push)

Bypasses are visually flagged in the GitHub UI on the PR and in the audit log — no silent exceptions.

## Out of Scope

- Build quality improvements (HTML validation, pinned deps) — separate iteration
- Cloudflare improvements — separate iteration
- `gh` CLI usage beyond auth setup — covered naturally in future workflow use
