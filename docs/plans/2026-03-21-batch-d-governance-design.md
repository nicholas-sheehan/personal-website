# Batch D — Governance & Audit Controls: Design Spec

**Date:** 2026-03-21
**Status:** Approved for implementation

---

## Overview

Batch D treats the repository as production-grade infrastructure with banking-standard controls. It consists of four implemented items and one explicitly decided-against item.

---

## Item 1: Node 24 Actions Bumps

### What

GitHub is forcing Node 24 as the default Actions runner from June 2026. All first-party GitHub Actions in `build.yml` must be on versions that ship with a Node 24 runner.

### Scope

Five actions in `.github/workflows/build.yml`:

| Action | Current tag | Target |
|--------|------------|--------|
| `actions/checkout` | `@v4` | Latest Node 24-compatible v4 release |
| `actions/setup-python` | `@v5` | Latest Node 24-compatible v5 release |
| `actions/upload-artifact` | `@v4` | Latest Node 24-compatible v4 release |
| `actions/download-artifact` | `@v4` | Latest Node 24-compatible v4 release |
| `actions/cache` | `@v4` | Latest Node 24-compatible v4 release |

`cloudflare/wrangler-action@v3` is out of scope — Cloudflare's own release cadence.

### Strategy

Keep major version tags with explicit patch version pins (e.g. `@v4.2.2`) rather than SHA pinning — appropriate for a personal project. Verify each target version is confirmed Node 24-compatible in its release notes or GitHub's deprecation notice.

### Acceptance criteria

- All five actions updated in `build.yml`
- CI passes on `staging` push

---

## Item 2: SSH Commit Signing (Personal Commits)

### What

All local commits by Nicholas should show a "Verified" badge on GitHub. Uses the existing `id_ed25519_github` ED25519 key already registered for authentication and stored in the 1Password SSH agent.

### Git config changes (global)

```
gpg.format = ssh
user.signingkey = <path-to-public-key or ssh-agent socket>
commit.gpgsign = true
```

The `user.signingkey` value must point to the public key file (e.g. `~/.ssh/id_ed25519_github.pub`) or use the `key::` prefix with the raw public key string. With 1Password SSH agent, the public key `.pub` file is typically available at `~/.ssh/` — confirm path at implementation time.

### GitHub registration

Settings → SSH and GPG keys → **New signing key** → paste the same public key already registered as an auth key. GitHub allows the same key under two separate entries (authentication vs. signing).

### Acceptance criteria

- `git log --show-signature` shows a valid SSH signature on new commits
- New commits pushed to GitHub show "Verified" badge
- Existing commits are unaffected (signing is not retroactive)

---

## Item 3: Direct Push Detector

### What

A GitHub Actions workflow that fires on every push to `main`. If the push was made by a human (not `github-actions[bot]`), it opens a GitHub Issue on the repo. As repo owner, Nicholas receives an automatic GitHub notification email.

This catches any admin bypass of the branch protection ruleset that results in a direct commit to `main`.

### New file: `.github/workflows/push-detector.yml`

```yaml
name: Direct push detector

on:
  push:
    branches: [main]

permissions:
  issues: write

jobs:
  detect:
    if: ${{ github.event.head_commit.author.name != 'github-actions[bot]' && !startsWith(github.event.head_commit.message, 'Merge pull request') }}
    runs-on: ubuntu-latest
    steps:
      - name: Open alert issue
        uses: actions/github-script@v7
        with:
          script: |
            const short = context.sha.slice(0, 7);
            await github.rest.issues.create({
              owner: context.repo.owner,
              repo: context.repo.repo,
              title: `⚠️ Direct push to main by ${context.actor} (${short})`,
              body: [
                `**Commit:** ${context.sha}`,
                `**Actor:** @${context.actor}`,
                `**Ref:** ${context.ref}`,
                `**Workflow run:** ${context.serverUrl}/${context.repo.owner}/${context.repo.repo}/actions/runs/${context.runId}`,
                ``,
                `This commit was pushed directly to \`main\` without going through a pull request. `,
                `If this was intentional (e.g. an authorised admin bypass), close this issue. `,
                `If it was not expected, investigate immediately.`,
              ].join('\n'),
            });
```

### Behaviour

- Bot commits are excluded via `github.event.head_commit.author.name != 'github-actions[bot]'`. Note: `github.actor` is NOT used here — when the bot pushes via `BOT_DEPLOY_KEY`, `github.actor` resolves to the deploy key owner (nicholas-sheehan), not `github-actions[bot]`. The git author name (set via `git config user.name "github-actions[bot]"` in the build workflow) is the reliable signal.
- PR merge commits are excluded via `!startsWith(github.event.head_commit.message, 'Merge pull request')` — the normal staging→main merge flow (merge commit strategy, never squash) always produces this commit message prefix.
- Only genuine direct pushes to `main` by a human that are not PR merges trigger an issue.
- Uses the built-in `GITHUB_TOKEN` (no extra secrets). Requires `issues: write` permission declared at workflow level.
- No `labels` field — avoids a 422 error if the `security` label doesn't exist.
- The `if:` expression uses full `${{ }}` syntax as required for job-level conditions (step-level conditions tolerate the bare form, but job-level does not).

### Acceptance criteria

- A genuine direct push to `main` by a human creates an issue
- Bot commits (daily build) do not create an issue
- Normal PR merges from `staging` do not create an issue
- Issue body contains commit SHA, actor, and run link

---

## Item 4: Ruleset Bypass Alerting — Decided Against

### Rationale

`repository_ruleset_bypass` is a GitHub webhook event but is not a supported GitHub Actions workflow trigger. The alternative — a scheduled workflow polling the GitHub Audit Log API — requires:

- A fine-grained PAT with audit log read access (new secret)
- State tracking to avoid duplicate alerts across runs
- Scheduled polling with inherent latency

On a solo project, this engineering overhead has low signal value. The direct push detector (Item 3) already catches the most consequential bypass: a human commit landing on `main` without a PR. Ruleset bypass events that don't result in a commit (e.g. a blocked force-push attempt) are low-risk and are already logged in the GitHub audit log, accessible on demand.

**Decision:** Mark as "decided against" in the roadmap with this rationale. Revisit if the project gains collaborators or if a bypass incident occurs.

---

## Item 5: Bot Commit Signing (GPG)

### What

The `github-actions[bot]` commits that update `index.html`, `og-image.png`, and `.og-image-hash` should show "Verified" on GitHub. This uses a dedicated GPG key with no passphrase, stored as a GitHub Secret.

### One-time setup (local, at implementation time)

1. Generate GPG key:
   ```
   gpg --batch --gen-key <<EOF
   Key-Type: RSA
   Key-Length: 4096
   Name-Real: github-actions[bot]
   Name-Email: github-actions[bot]@users.noreply.github.com
   Expire-Date: 0
   %no-passphrase
   EOF
   ```
2. Export private key: `gpg --export-secret-keys --armor <KEY_ID> > bot-gpg.key`
3. Add as GitHub Secret `BOT_GPG_KEY` (paste armored private key)
4. Export public key: `gpg --export --armor <KEY_ID>`
5. Register public key on GitHub: Settings → GPG keys → New GPG key (this is on Nicholas's account — GitHub marks commits by `github-actions[bot]@users.noreply.github.com` as verified when the key is registered to any account that has push access)
6. Delete local `bot-gpg.key` file — key material should not persist on disk

### Workflow changes in `build.yml`

Add two steps before the "Commit updated index.html" step:

```yaml
- name: Import bot GPG key
  run: echo "${{ secrets.BOT_GPG_KEY }}" | gpg --batch --import

- name: Configure git signing
  run: |
    GPG_KEY_ID=$(gpg --list-secret-keys --keyid-format LONG \
      "github-actions[bot]@users.noreply.github.com" \
      | grep '^sec' | awk '{print $2}' | cut -d'/' -f2)
    git config user.signingkey "$GPG_KEY_ID"
    git config gpg.program gpg
    git config commit.gpgsign true
```

Notes:
- The email is quoted to prevent `[bot]` being interpreted as a shell glob character class.
- `git config` here is local (no `--global`) — settings apply only within this workflow run, not globally on the runner. This is correct and intentional.
- The existing `git config user.name` and `user.email` lines stay. The `git diff --cached --quiet || git commit -m "..."` line automatically uses signing because `commit.gpgsign = true` is now set.
- `GNUPGHOME` is not set explicitly — the runner's default `~/.gnupg/` is used for both the import step and the commit step. This is consistent on `ubuntu-latest`.

### Acceptance criteria

- Bot commits on `main` show "Verified" badge on GitHub
- CI does not error when no content changed (signing only affects the commit step, which is already skipped via `git diff --cached --quiet`)
- Key ID extraction is reliable (tested against GPG output format)

---

## Out of Scope

- `cloudflare/wrangler-action` version bumps — Cloudflare's own cadence
- SHA pinning of Actions — appropriate for enterprise, overkill for personal project
- `security` label creation — `labels` field removed from push-detector script entirely to avoid 422 errors; issue title prefix `⚠️` provides sufficient visual distinction
- Retroactive commit signing — signing only applies to new commits

---

## Implementation Order

1. Node 24 bumps (lowest risk, no secrets, fastest CI feedback)
2. SSH commit signing (local git config only, no CI changes)
3. Bot commit signing (new secret + workflow changes)
4. Direct push detector (new workflow file)

Items 2 and 3 can be done in either order but 2 should be done first so the implementation commits themselves are signed.
