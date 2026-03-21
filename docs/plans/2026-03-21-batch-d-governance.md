# Batch D — Governance & Audit Controls Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Harden the repo with signed commits (personal and bot), Node 24 Actions compatibility, and a direct-push detector that opens a GitHub Issue on any non-PR commit to `main`.

**Architecture:** Four independent changes — (1) version bumps to `build.yml`, (2) local git config for SSH signing, (3) GPG key as GitHub Secret + workflow changes for bot signing, (4) new `push-detector.yml` workflow. No application code changes; verification is through CI and GitHub UI.

**Tech Stack:** GitHub Actions, GPG, SSH commit signing, `actions/github-script`

**Design spec:** `docs/plans/2026-03-21-batch-d-governance-design.md`

---

## Chunk 1: Node 24 Actions bumps + SSH commit signing

### Task 1: Research current Node 24-compatible action versions

**Files:**
- Read: `.github/workflows/build.yml`

The current workflow pins `@v4` floating tags. GitHub is deprecating Node 20 in Actions runners from June 2026. We need the latest patch-pinned versions of each action that ship Node 24 support.

- [ ] **Step 1.1: Look up latest release for each action**

  Visit the releases page (or run `gh release list`) for each action and record the latest version tag:

  ```bash
  gh release list --repo actions/checkout --limit 5
  gh release list --repo actions/setup-python --limit 5
  gh release list --repo actions/upload-artifact --limit 5
  gh release list --repo actions/download-artifact --limit 5
  gh release list --repo actions/cache --limit 5
  ```

  Record the latest `vX.Y.Z` tag for each. Confirm in the release notes that the release targets Node 20 or Node 24 (not Node 16). Any release from mid-2024 onward for these actions uses Node 20 at minimum; releases from late 2025 onward may explicitly target Node 24. Use whatever is latest at implementation time.

  > Note: `cloudflare/wrangler-action@v3` is **out of scope** — skip it.

---

### Task 2: Update action versions in `build.yml`

**Files:**
- Modify: `.github/workflows/build.yml`

- [ ] **Step 2.1: Update the five action version pins**

  Using the versions recorded in Task 1, update `.github/workflows/build.yml`. The five locations to change (current values shown for reference):

  | Line (approx) | Current | Change to |
  |----------------|---------|-----------|
  | `uses: actions/checkout@v4` (build job) | `@v4` | `@vX.Y.Z` |
  | `uses: actions/setup-python@v5` | `@v5` | `@vX.Y.Z` |
  | `uses: actions/upload-artifact@v4` | `@v4` | `@vX.Y.Z` |
  | `uses: actions/download-artifact@v4` | `@v4` | `@vX.Y.Z` |
  | `uses: actions/cache@v4` (pip cache) | `@v4` | `@vX.Y.Z` |
  | `uses: actions/cache@v4` (npm cache) | `@v4` | same version as above |
  | `uses: actions/checkout@v4` (deploy job, Worker source) | `@v4` | same as first checkout |

  There are **two `actions/checkout` usages** and **two `actions/cache` usages** in the file — update all of them to the same version.

- [ ] **Step 2.2: Verify no other first-party actions were missed**

  ```bash
  grep 'uses: actions/' .github/workflows/build.yml
  ```

  Expected output: only the 5 distinct actions listed above. Confirm none were overlooked.

- [ ] **Step 2.3: Commit**

  ```bash
  git add .github/workflows/build.yml
  git commit -m "ci: bump GitHub Actions to latest Node 24-compatible versions"
  ```

---

### Task 3: Configure SSH commit signing locally

**Files:**
- None in the repo — this is local git config only.

SSH signing uses the existing `id_ed25519_github` key in 1Password. The public key is already on disk at `~/.ssh/id_ed25519_github.pub` (it was registered as an auth key during the SSH remote setup in Batch A). The 1Password SSH agent handles the actual signing operation via its socket.

- [ ] **Step 3.1: Confirm the public key file exists**

  ```bash
  cat ~/.ssh/id_ed25519_github.pub
  ```

  Expected: a single line starting with `ssh-ed25519 AAAA...`. If the file doesn't exist, export it from 1Password: open 1Password → find the SSH key item → copy the public key → save to `~/.ssh/id_ed25519_github.pub`.

- [ ] **Step 3.2: Configure git for SSH signing**

  ```bash
  git config --global gpg.format ssh
  git config --global user.signingkey ~/.ssh/id_ed25519_github.pub
  git config --global commit.gpgsign true
  ```

- [ ] **Step 3.3: Create the allowed signers file for local verification**

  `git log --show-signature` needs an `allowed_signers` file to verify SSH signatures locally. Without it, git can sign but not display "Good signature" on inspection.

  ```bash
  mkdir -p ~/.config/git
  echo "$(git config --global user.email) namespaces=\"git\" $(cat ~/.ssh/id_ed25519_github.pub)" \
    > ~/.config/git/allowed_signers
  git config --global gpg.ssh.allowedSignersFile ~/.config/git/allowed_signers
  ```

  The `namespaces="git"` restricts this key to the git signing namespace (SSH signing best practice).

- [ ] **Step 3.4: Register the signing key on GitHub**

  1. Go to **github.com → Settings → SSH and GPG keys**
  2. Click **New signing key** (separate from "New authentication key")
  3. Title: `id_ed25519_github (signing)`
  4. Paste the contents of `~/.ssh/id_ed25519_github.pub`
  5. Click **Add SSH key**

  GitHub now knows to mark commits from this key as "Verified". The same physical key can be registered for both authentication and signing — they appear as two separate entries in the UI.

- [ ] **Step 3.5: Make a test commit and verify**

  Make any trivial local change (e.g. add a space and remove it in a non-deployed file), commit, and check the signature:

  ```bash
  git log --show-signature -1
  ```

  Expected output includes:
  ```
  Good "git" signature for <your-email> with ED25519 key SHA256:...
  ```

  Push to `staging` and check `github.com/nicholas-sheehan/personal-website/commits/staging` — the new commit should show a **Verified** badge. If it shows "Unverified", the signing key may not be registered on GitHub yet (Step 3.4).

  > **Note:** Existing commits will not show Verified — signing is not retroactive. Only new commits from this point forward are signed.

---

## Chunk 2: Bot commit signing + push detector

### Task 4: Generate the bot GPG key

**Files:**
- None in the repo — key generation is local only, key material goes to GitHub Secrets.

- [ ] **Step 4.1: Generate the GPG key**

  Run this command verbatim. The heredoc creates a key for `github-actions[bot]@users.noreply.github.com` with no passphrase and no expiry:

  ```bash
  gpg --batch --gen-key <<'EOF'
  Key-Type: RSA
  Key-Length: 4096
  Name-Real: github-actions[bot]
  Name-Email: github-actions[bot]@users.noreply.github.com
  Expire-Date: 0
  %no-passphrase
  %commit
  EOF
  ```

  Expected output: `gpg: key XXXXXXXX marked as ultimately trusted` — note the 8-character short key ID in the output (you'll need the long form in the next step).

- [ ] **Step 4.2: Get the full key ID**

  ```bash
  gpg --list-secret-keys --keyid-format LONG "github-actions[bot]@users.noreply.github.com"
  ```

  Expected output format:
  ```
  sec   rsa4096/AABBCCDD11223344 2026-03-21 [SC]
        <fingerprint>
  uid           [ultimate] github-actions[bot] <github-actions[bot]@users.noreply.github.com>
  ```

  The long key ID is the hex string after `rsa4096/` — e.g. `AABBCCDD11223344`. Copy it.

- [ ] **Step 4.3: Export the private key**

  ```bash
  gpg --export-secret-keys --armor AABBCCDD11223344 > /tmp/bot-gpg.key
  ```

  Replace `AABBCCDD11223344` with your actual key ID.

- [ ] **Step 4.4: Export the public key**

  ```bash
  gpg --export --armor AABBCCDD11223344
  ```

  Copy the output (the full `-----BEGIN PGP PUBLIC KEY BLOCK-----` block).

---

### Task 5: Register key on GitHub and add secret

- [ ] **Step 5.1: Add `BOT_GPG_KEY` as a GitHub Secret**

  1. `cat /tmp/bot-gpg.key` — copy the full armored private key block
  2. Go to **github.com/nicholas-sheehan/personal-website → Settings → Secrets and variables → Actions**
  3. Click **New repository secret**
  4. Name: `BOT_GPG_KEY`
  5. Value: paste the full armored private key (the `-----BEGIN PGP PRIVATE KEY BLOCK-----` block)
  6. Click **Add secret**

- [ ] **Step 5.2: Register the public key on GitHub**

  1. Go to **github.com → Settings → SSH and GPG keys → New GPG key**
  2. Title: `github-actions[bot] signing key`
  3. Paste the public key from Step 4.4
  4. Click **Add GPG key**

  GitHub will mark commits signed with this key as "Verified" because the key is registered on an account that has push access to the repo.

- [ ] **Step 5.3: Delete the private key file**

  ```bash
  rm /tmp/bot-gpg.key
  ```

  Key material must not persist on disk. Verify:

  ```bash
  ls /tmp/bot-gpg.key
  ```

  Expected: `No such file or directory`

---

### Task 6: Add GPG signing steps to `build.yml`

**Files:**
- Modify: `.github/workflows/build.yml`

Two new steps must be inserted **before** the "Commit updated index.html" step (currently around line 51).

- [ ] **Step 6.1: Add the import and config steps**

  In `.github/workflows/build.yml`, locate:
  ```yaml
        - name: Commit updated index.html
          run: |
            git config user.name "github-actions[bot]"
  ```

  Insert the following two steps immediately before it:

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

  The `git config` calls here are **local** (no `--global`) — they apply only within this workflow run. The existing `git config user.name` and `user.email` lines remain unchanged. Because `commit.gpgsign true` is now set, the subsequent `git commit` line automatically signs.

- [ ] **Step 6.2: Verify the indentation and structure**

  The two new steps should be at the same indentation level as all other `- name:` steps in the `build` job. Run:

  ```bash
  python3 -c "import yaml; yaml.safe_load(open('.github/workflows/build.yml'))"
  ```

  Expected: no output (valid YAML). Any `yaml.scanner.ScannerError` means an indentation problem — fix it before continuing.

- [ ] **Step 6.3: Commit**

  ```bash
  git add .github/workflows/build.yml
  git commit -m "ci: sign bot commits with GPG key"
  ```

---

### Task 7: Create the direct push detector workflow

**Files:**
- Create: `.github/workflows/push-detector.yml`

- [ ] **Step 7.1: Create the workflow file**

  Create `.github/workflows/push-detector.yml` with the following exact content:

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
                  `This commit was pushed directly to \`main\` without going through a pull request.`,
                  `If this was intentional (e.g. an authorised admin bypass), close this issue.`,
                  `If it was not expected, investigate immediately.`,
                ].join('\n'),
              });
  ```

  > **Why `head_commit.author.name` not `github.actor`:** When the CI bot pushes via `BOT_DEPLOY_KEY`, GitHub resolves `github.actor` to the deploy key owner (nicholas-sheehan), not `github-actions[bot]`. The git author name set by `git config user.name "github-actions[bot]"` in the build workflow is the reliable signal.
  >
  > **Why the `Merge pull request` check:** PR merges (your normal staging→main flow) use merge commit strategy, always producing this commit message prefix. Without this exclusion, every legitimate PR merge would trigger a false alarm.

- [ ] **Step 7.2: Validate YAML**

  ```bash
  python3 -c "import yaml; yaml.safe_load(open('.github/workflows/push-detector.yml'))"
  ```

  Expected: no output.

- [ ] **Step 7.3: Commit**

  ```bash
  git add .github/workflows/push-detector.yml
  git commit -m "ci: add direct push detector workflow"
  ```

---

## Chunk 3: Verification and docs

### Task 8: Push to staging and verify CI

- [ ] **Step 8.1: Restore CI artifacts and sync with main before pushing**

  Batch D makes no changes to `index.html`, so restore it along with the pure CI artifacts to avoid a rebase conflict on the bot's `<!-- updated:start/end -->` timestamp marker:

  ```bash
  git restore og-image.png sitemap.xml index.html
  git pull --rebase origin main
  git pull --rebase origin staging
  ```

  Resolve any rebase conflict on `<!-- updated:start/end -->` by keeping your HTML structure and the bot's (newer) timestamp text.

- [ ] **Step 8.2: Push to staging**

  ```bash
  git push origin staging
  ```

- [ ] **Step 8.3: Verify CI on staging**

  Monitor the Actions run at `github.com/nicholas-sheehan/personal-website/actions`. Both the build job and deploy job must pass. Specifically confirm:

  - The action version bumps don't break anything
  - The GPG import step runs without error
  - The "Configure git signing" step runs and the subsequent commit step succeeds (or is skipped when no content changed — both are correct)
  - The push-detector workflow does NOT fire on a staging push (it only triggers on `main`)

  > If the GPG import step fails with "no secret key data", the `BOT_GPG_KEY` secret may not have been saved correctly. Re-export the key with `gpg --export-secret-keys --armor` and re-save the secret.

- [ ] **Step 8.4: Verify bot commit signing on a real build**

  After a successful CI run on `main` that produces a bot commit (either trigger manually via `workflow_dispatch` or wait for the daily scheduled run), navigate to `github.com/nicholas-sheehan/personal-website/commits/main` and confirm the bot commit shows a **Verified** badge.

  > If it shows "Unverified": check that the public key was registered on GitHub (Task 5.2) and that the email in the GPG key (`github-actions[bot]@users.noreply.github.com`) exactly matches the GitHub noreply email format.

---

### Task 9: Update docs (do this BEFORE the final commit)

**Files:**
- Modify: `docs/roadmap.md`

Per project workflow, docs must be committed in the **same commit** as the code they document — never as a follow-up. Run the docs-update skill first, then bundle everything into one final commit.

- [ ] **Step 9.1: Mark Batch D complete in the roadmap**

  In `docs/roadmap.md`, find the `**Batch D**` section and:

  1. Mark all four implemented items as `[x]`
  2. Add `✅ done YYYY-MM-DD` to the batch heading (replace YYYY-MM-DD with today's date)
  3. Add the ruleset bypass alerting item to the "Discussed and decided against" section at the bottom:
     ```
     - Ruleset bypass alerting — `repository_ruleset_bypass` is not a GitHub Actions workflow trigger. Polling the audit log adds complexity (PAT + state tracking) with low signal for a solo project; direct push detector covers the consequential case.
     ```

- [ ] **Step 9.2: Run the docs-update skill**

  Invoke the `docs-update` skill to check all required doc files (roadmap, architecture, README, MEMORY.md, build.py docstring). Batch D adds no new external APIs or data sources, so architecture/README/build.py are likely unchanged — but confirm via the skill before committing.

- [ ] **Step 9.3: Commit all staged changes (code + docs together)**

  Stage everything that isn't already committed:

  ```bash
  git status
  git add docs/roadmap.md
  # add any other files flagged by docs-update (MEMORY.md, etc.)
  git commit -m "docs: mark Batch D complete"
  ```

  If Tasks 2, 6, and 7 have already been committed individually (which is the standard flow), this docs commit is the final commit on the branch.

---

### Task 10: Open PR to main

- [ ] **Step 10.1: Final pre-PR checks**

  ```bash
  git status       # should be clean
  git log --oneline origin/main..HEAD   # shows your batch D commits
  ```

- [ ] **Step 10.2: Open PR**

  ```bash
  /opt/homebrew/bin/gh pr create \
    --base main \
    --head staging \
    --title "Batch D — Governance & audit controls" \
    --body "$(cat <<'EOF'
  ## Summary

  - Bump GitHub Actions to latest Node 24-compatible patch versions (`checkout`, `setup-python`, `upload-artifact`, `download-artifact`, `cache`)
  - Configure SSH commit signing for personal commits (local git config + 1Password key)
  - Sign bot commits with a dedicated GPG key (`BOT_GPG_KEY` secret) — bot commits now show Verified on GitHub
  - Add direct push detector workflow — opens a GitHub Issue if a human pushes directly to `main` outside of a PR merge

  Ruleset bypass alerting was scoped and decided against (not a supported Actions workflow trigger; direct push detector covers the consequential case).

  ## Test plan

  - [ ] CI passes on staging (all jobs green)
  - [ ] Action version bumps don't introduce regressions
  - [ ] GPG import step succeeds in CI
  - [ ] Bot commit on main shows Verified badge
  - [ ] Push detector workflow does not fire on PR merge
  - [ ] Personal commits show Verified badge on GitHub

  🤖 Generated with [Claude Code](https://claude.com/claude-code)
  EOF
  )"
  ```

- [ ] **Step 10.3: Merge using merge commit (not squash)**

  In the GitHub PR UI, use **"Create a merge commit"** — not squash, not rebase. This is required to keep `staging` in sync without rebase conflicts on future syncs. See `docs/pipeline.md`.

---

## Notes

- **SSH signing verification**: `git log --show-signature -1` shows signature details locally. GitHub shows Verified badge only after push.
- **Push detector false positives**: The first time you merge this PR, the push-detector workflow will fire (your first post-setup commit to `main` is a PR merge, which is excluded — but verify this in CI). Close any unexpected alert issues.
- **GPG key rotation**: If `BOT_GPG_KEY` is ever compromised, generate a new key, update the secret, register the new public key on GitHub, and revoke the old one via GitHub Settings.
- **Push detector testing**: The only way to fully test it is to intentionally push directly to `main` (which requires admin bypass). After the first legitimate direct push (if one ever occurs), you'll know it works by the alert issue appearing.
