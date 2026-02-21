# nicsheehan.com

Personal website for Nicholas Sheehan. A static site that pulls all its content from external services, rebuilt daily by GitHub Actions.

## How it works

`build.py` fetches data from five sources, injects it into `index.html`, and GitHub Pages serves the result. A GitHub Actions workflow runs this daily at 9am AEDT / 8am AEST, commits any changes, and deploys.

## Content sources

| What | Service | How to update |
|------|---------|---------------|
| **Site metadata** | `site.toml` | Edit `site.toml` — title, description, OG tags, analytics, and data source URLs. `site.title` and `site.description` are reused for OG and Twitter tags. See inline comments in the file for details. Push or run the build to apply. |
| **Name, bio, tagline, avatar** | [Gravatar](https://gravatar.com/profile) | Edit your Gravatar profile. Name, job title, company, location, and description are all pulled automatically. |
| **Nav links** | [Gravatar](https://gravatar.com/profile) | Add/remove/reorder links on your Gravatar profile. Email is pulled from Gravatar contact info. |
| **Currently reading** | [Goodreads](https://www.goodreads.com) | Update your "Currently Reading" shelf on Goodreads. The site reads your public RSS feed. |
| **Recently watched** | [Letterboxd](https://letterboxd.com) | Log and rate films on Letterboxd. The 8 most recent entries are shown via RSS. |
| **Reads I recommend** | [Instapaper](https://www.instapaper.com) | Star articles in Instapaper. The 5 most recent starred articles are shown. |
| **Listening to lately** | [Last.fm](https://www.last.fm) | Your top 8 tracks of the current month are pulled automatically via the Last.fm API. |

## When does the site update?

- **Automatically** every day at 9am AEDT / 8am AEST via GitHub Actions
- **On every push** to the `main` branch
- **Manually** from the [Actions tab](https://github.com/nicholas-sheehan/personal-website/actions/workflows/build.yml) → "Run workflow"

## GitHub secrets

These are configured in the repo under Settings → Secrets and variables → Actions:

| Secret | Purpose |
|--------|---------|
| `GRAVATAR_API_KEY` | Authenticates with Gravatar API to access links and contact info |
| `INSTAPAPER_CONSUMER_KEY` | Instapaper OAuth consumer key |
| `INSTAPAPER_CONSUMER_SECRET` | Instapaper OAuth consumer secret |
| `INSTAPAPER_OAUTH_TOKEN` | Instapaper user token (generated via `build.py auth`) |
| `INSTAPAPER_OAUTH_TOKEN_SECRET` | Instapaper user token secret |
| `LASTFM_API_KEY` | Last.fm API key (get one at last.fm/api/account/create) |

## Running locally

```bash
# Full build (requires env vars for Gravatar, Instapaper, and Last.fm)
GRAVATAR_API_KEY="your-key" \
INSTAPAPER_CONSUMER_KEY="your-key" \
INSTAPAPER_CONSUMER_SECRET="your-secret" \
INSTAPAPER_OAUTH_TOKEN="your-token" \
INSTAPAPER_OAUTH_TOKEN_SECRET="your-secret" \
LASTFM_API_KEY="your-key" \
python3 build.py
```

Goodreads and Letterboxd use public RSS feeds and work without any credentials.

## Files

| File | Purpose |
|------|---------|
| `site.toml` | Site config — metadata, OG tags, analytics, and data source URLs. Read by `build.py` at build time. |
| `index.html` | The site. Contains comment markers (`<!-- tag:start/end -->`) where build.py injects content. |
| `style.css` | Styling. |
| `build.py` | Build script that fetches all data and updates index.html. |
| `CNAME` | Custom domain config for GitHub Pages. |
| `.github/workflows/build.yml` | GitHub Actions workflow for scheduled builds and deployment. |
