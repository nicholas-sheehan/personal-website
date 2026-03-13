# Release Workflow Hardening Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Set up SSH authentication, install `gh` CLI, create a dedicated deploy key for the build bot, and re-enable branch protection on `main` via a GitHub Ruleset.

**Architecture:** Personal SSH key authenticates the developer's git operations. A separate deploy key (stored as a GitHub Secret) is used exclusively by the CI bot to push build output. A GitHub Ruleset enforces PR-before-merge on `main` with bypass actors for the deploy key and repo admin.

**Tech Stack:** OpenSSH (`ssh-keygen`), Homebrew, `gh` CLI, GitHub Actions (`actions/checkout@v4`), GitHub Rulesets API (web UI)

---

## Chunk 1: Local SSH Setup + `gh` CLI

### Task 1: Generate personal SSH key

**Files:** None — local machine config only

- [ ] **Step 1: Check for existing SSH keys**

```bash
ls ~/.ssh/
```

Expected: Either no `.ssh` directory or no `id_ed25519` file. If `id_ed25519` already exists, skip to Task 2.

- [ ] **Step 2: Generate the key**

```bash
ssh-keygen -t ed25519 -C "your@email.com"
```

When prompted:
- File location: press Enter to accept default (`~/.ssh/id_ed25519`)
- Passphrase: enter a strong passphrase (or press Enter for none — passphrase is optional but recommended)

Expected output:
```
Your identification has been saved in /Users/<you>/.ssh/id_ed25519
Your public key has been saved in /Users/<you>/.ssh/id_ed25519.pub
```

- [ ] **Step 3: Start the SSH agent and add the key**

```bash
eval "$(ssh-agent -s)"
ssh-add ~/.ssh/id_ed25519
```

Expected: `Identity added: /Users/<you>/.ssh/id_ed25519`

- [ ] **Step 4: Copy the public key**

```bash
cat ~/.ssh/id_ed25519.pub
```

Copy the entire output (starts with `ssh-ed25519`, ends with your email).

- [ ] **Step 5: Add public key to GitHub**

In browser:
1. Go to GitHub → Settings → SSH and GPG keys → New SSH key
2. Title: `Mac` (or any label you'll recognise)
3. Key type: Authentication Key
4. Paste the public key
5. Click Add SSH key

- [ ] **Step 6: Verify the connection**

```bash
ssh -T git@github.com
```

Expected: `Hi nicholas-sheehan! You've successfully authenticated, but GitHub does not provide shell access.`

---

### Task 2: Switch git remote to SSH

**Files:** None — local repo config only

- [ ] **Step 1: Check current remote**

```bash
cd "/Users/nicholassheehan/Documents/Claude Files/Personal website"
git remote -v
```

Expected: HTTPS remote, e.g. `origin  https://github.com/nicholas-sheehan/personal-website.git`

- [ ] **Step 2: Switch to SSH**

```bash
git remote set-url origin git@github.com:nicholas-sheehan/personal-website.git
```

- [ ] **Step 3: Verify**

```bash
git remote -v
```

Expected: `origin  git@github.com:nicholas-sheehan/personal-website.git (fetch/push)`

- [ ] **Step 4: Test with a dry-run fetch**

```bash
git fetch origin
```

Expected: No errors. If it prompts about host authenticity, type `yes`.

---

### Task 3: Install `gh` CLI + authenticate

**Files:** None — local machine config only

- [ ] **Step 1: Install via Homebrew**

```bash
brew install gh
```

Expected: Installs successfully. Takes 1–2 minutes.

- [ ] **Step 2: Verify install**

```bash
gh --version
```

Expected: `gh version X.Y.Z (...)` — any recent version is fine.

- [ ] **Step 3: Authenticate**

```bash
gh auth login
```

Walk through the interactive prompts:
- Account: GitHub.com
- Protocol: SSH
- SSH key: select the `id_ed25519` key you just created
- Authenticate: Login with a web browser (follow the one-time code flow)

- [ ] **Step 4: Verify authentication**

```bash
gh auth status
```

Expected:
```
github.com
  ✓ Logged in to github.com as nicholas-sheehan
  ✓ Git operations for github.com configured to use ssh protocol
```

---

## Chunk 2: Deploy Key + CI Update

### Task 4: Generate deploy key pair

**Files:** Temporary — key files generated then cleaned up

- [ ] **Step 1: Generate the deploy key (separate from personal key)**

```bash
ssh-keygen -t ed25519 -C "github-actions-bot" -f /tmp/deploy_key -N ""
```

Flags:
- `-f /tmp/deploy_key` — saves to `/tmp/` (not `~/.ssh/`, this key is for the bot not you)
- `-N ""` — no passphrase (required for automated CI use)

Expected: Creates `/tmp/deploy_key` (private) and `/tmp/deploy_key.pub` (public)

- [ ] **Step 2: Display the public key — copy it**

```bash
cat /tmp/deploy_key.pub
```

Copy the output.

- [ ] **Step 3: Add public key to repo as a deploy key**

In browser:
1. Go to `github.com/nicholas-sheehan/personal-website` → Settings → Deploy keys → Add deploy key
2. Title: `Build Bot`
3. Key: paste the public key
4. Check "Allow write access"
5. Click Add key

Note the deploy key's numeric ID from the URL after saving (e.g. `github.com/.../settings/keys/12345678`) — needed for the Ruleset bypass in Task 6.

- [ ] **Step 4: Add private key as a GitHub Secret**

```bash
gh secret set BOT_DEPLOY_KEY < /tmp/deploy_key
```

Expected: `✓ Set Actions secret BOT_DEPLOY_KEY for nicholas-sheehan/personal-website`

- [ ] **Step 5: Clean up local key files**

```bash
rm /tmp/deploy_key /tmp/deploy_key.pub
```

The private key now lives only in GitHub Secrets. Do not commit it anywhere.

---

### Task 5: Update `build.yml` to use deploy key

**Files:**
- Modify: `.github/workflows/build.yml`

- [ ] **Step 1: Verify current permissions block**

Open `.github/workflows/build.yml`. Confirm line 13 reads:
```yaml
permissions:
  contents: write
```

This grants `GITHUB_TOKEN` write access — no longer needed once the deploy key handles pushes.

- [ ] **Step 2: Update permissions and checkout in the build job**

Change the `permissions` block and the `build` job's checkout step:

**Before:**
```yaml
permissions:
  contents: write

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
```

**After:**
```yaml
permissions:
  contents: read

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          ssh-key: ${{ secrets.BOT_DEPLOY_KEY }}
```

The `ssh-key` parameter configures git in the runner to use the deploy key for all subsequent git operations (including `git push`).

- [ ] **Step 3: Verify the rest of the build job is unchanged**

The "Commit updated index.html" step remains exactly as-is — the `git push` command now uses the deploy key automatically via the SSH agent configured by checkout.

Note: the `deploy` job also has a `actions/checkout@v4` step — it does NOT need `ssh-key` added. It only reads (git pull) and never pushes, so the default `GITHUB_TOKEN` (read-only after our permissions change) is sufficient.

- [ ] **Step 4: Commit**

```bash
git add .github/workflows/build.yml
git commit -m "ci: use deploy key for bot push instead of GITHUB_TOKEN"
```

- [ ] **Step 5: Push to staging and verify CI passes**

```bash
git push origin staging
```

Open GitHub Actions tab and confirm the build job completes successfully, including the "Commit updated index.html" push step. If the bot has no changes to commit, that's fine — the `git diff --cached --quiet || git commit` guard handles it.

---

## Chunk 3: Branch Protection Ruleset

### Task 6: Create GitHub Ruleset on `main`

**Files:** None — GitHub configuration only

This step is done via the GitHub web UI (the Rulesets API requires knowing the deploy key's numeric ID and the admin role ID, which are easier to confirm visually).

- [ ] **Step 1: Find the deploy key ID**

Go to `github.com/nicholas-sheehan/personal-website/settings/keys`. Note the numeric ID in the URL when you click on the "Build Bot" deploy key (e.g. `…/keys/12345678`).

- [ ] **Step 2: Create the Ruleset**

Go to `github.com/nicholas-sheehan/personal-website/settings/rules` → New ruleset → New branch ruleset.

Fill in:
- **Ruleset name:** `Protect main`
- **Enforcement status:** Active
- **Bypass list:** Add bypass actors:
  - Click "Add bypass" → Repository admin role → Allow always
  - Click "Add bypass" → Deploy key → find "Build Bot" → Allow always
- **Target branches:** Add target → Include by pattern → `main`
- **Rules:** Enable:
  - ✅ Restrict creations
  - ✅ Restrict deletions
  - ✅ Require a pull request before merging
    - Required approvals: 0 (solo project)
    - Uncheck all sub-options
  - ✅ Block force pushes

Click Save changes.

- [ ] **Step 3: Verify protection is active**

```bash
git checkout main
git pull --rebase origin main
git commit --allow-empty -m "test: verify branch protection"
git push origin main
```

Expected: Push is rejected with an error like:
```
remote: error: GH013: Repository rule violations found for refs/heads/main.
```

Clean up (discard the test commit locally):
```bash
git reset --soft HEAD~1
git checkout staging
```

- [ ] **Step 4: Verify bot can still push**

Trigger a manual workflow run:

```bash
gh workflow run build.yml
```

Wait for it to complete:
```bash
gh run watch
```

Expected: Build job completes and pushes successfully to `main` (or skips commit if no feed changes — both are correct).

- [ ] **Step 5: Update roadmap**

Mark the following items as done in `docs/roadmap.md`:
- `Restore main branch protection via GitHub Ruleset with deploy key bypass` ✅
- `Switch git remote from HTTPS to SSH` ✅
- `Install gh CLI properly` ✅

- [ ] **Step 6: Commit docs**

```bash
git add docs/roadmap.md
git commit -m "docs: mark SSH, gh CLI, and branch protection as complete"
git push origin staging
```

---

## Verification Checklist

After completing all tasks, confirm:

- [ ] `ssh -T git@github.com` responds with your username
- [ ] `git remote -v` shows SSH URL for origin
- [ ] `gh auth status` shows authenticated
- [ ] `BOT_DEPLOY_KEY` visible in repo Settings → Secrets → Actions
- [ ] "Build Bot" deploy key visible in repo Settings → Deploy keys (with write access)
- [ ] Direct push to `main` is rejected
- [ ] CI build job pushes to `main` successfully via deploy key
- [ ] Roadmap updated
