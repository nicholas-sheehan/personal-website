# nicsheehan.com

Personal website for Nicholas Sheehan. A static site that pulls all its content from external services and presents it as a Y2K-inspired personal dashboard, rebuilt daily by GitHub Actions.

## How it works

`build.py` fetches data from external services, injects it into `index.html`, and Cloudflare Pages serves the result. A GitHub Actions workflow runs this daily at 9am AEDT / 8am AEST, commits any changes, and deploys.

See [docs/architecture.md](docs/architecture.md) for a full diagram of the build and hosting stack, and [docs/pipeline.md](docs/pipeline.md) for the development workflow and branch strategy.

## Content sources

| What | Service | How to update |
|------|---------|---------------|
| **Site metadata** | `site.toml` | Edit `site.toml` — title, description, OG tags, analytics, and data source URLs. `site.title` and `site.description` are reused for OG and Twitter tags. See inline comments in the file for details. Push or run the build to apply. |
| **Name, bio, tagline, avatar** | [Gravatar](https://gravatar.com/profile) | Edit your Gravatar profile. Name, job title, company, location, and description are all pulled automatically. |
| **Nav links** | [Gravatar](https://gravatar.com/profile) | Add/remove/reorder links on your Gravatar profile. Email is pulled from Gravatar contact info. |
| **Currently reading** | [Goodreads](https://www.goodreads.com) | Update your "Currently Reading" shelf on Goodreads. The site reads your public RSS feed. |
| **Recently watched** | [Letterboxd](https://letterboxd.com) | Log and rate films on Letterboxd. The 5 most recent entries are shown via RSS. |
| **Reads I recommend** | [Instapaper](https://www.instapaper.com) | Star articles in Instapaper. The 5 most recent starred articles are shown. |
| **Listening to lately** | [Last.fm](https://www.last.fm) | Your top 5 tracks of the current month are pulled automatically via the Last.fm API. |
| **Film enrichment** | [TMDB](https://www.themoviedb.org) | Poster, director, and synopsis are fetched automatically for each film. Gracefully skipped if key is unset. |
| **Currently playing** | [Last.fm](https://www.last.fm) via Cloudflare Worker | Live now-playing / last-played track fetched at runtime by the browser. A Cloudflare Worker at `now-playing.b-tonic.workers.dev` proxies Last.fm `user.getRecentTracks`. Deployed separately — see [Worker deployment](#worker-deployment) below. |

## When does the site update?

- **Automatically** every day at 9am AEDT / 8am AEST via GitHub Actions
- **On every push** to `main` or `staging` (staging deploys to `staging.nicsheehan.pages.dev`)
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
| `LASTFM_API_KEY` | Last.fm API key for the static build (top-5 monthly tracks). A **separate copy** of this key is also stored as a Cloudflare secret for the now-playing Worker — see [Worker deployment](#worker-deployment). |
| `TMDB_READ_ACCESS_TOKEN` | TMDB API Read Access Token (v4) for film posters/director/synopsis — preferred over `TMDB_API_KEY`. Get from themoviedb.org/settings/api under "API Read Access Token". |
| `TMDB_API_KEY` | Legacy TMDB v3 API key — kept as fallback if `TMDB_READ_ACCESS_TOKEN` is unset |
| `CLOUDFLARE_API_TOKEN` | Cloudflare API token with "Cloudflare Pages: Edit" + "Workers Scripts: Edit" permissions — used by CI to deploy Pages and the now-playing Worker via wrangler |
| `CLOUDFLARE_ACCOUNT_ID` | Cloudflare account ID — used alongside the API token for Pages deployment |

## Running locally

```bash
# Full build (requires env vars for Gravatar, Instapaper, and Last.fm)
GRAVATAR_API_KEY="your-key" \
INSTAPAPER_CONSUMER_KEY="your-key" \
INSTAPAPER_CONSUMER_SECRET="your-secret" \
INSTAPAPER_OAUTH_TOKEN="your-token" \
INSTAPAPER_OAUTH_TOKEN_SECRET="your-secret" \
LASTFM_API_KEY="your-key" \
TMDB_READ_ACCESS_TOKEN="your-token" \
python3 build.py
```

Goodreads and Letterboxd use public RSS feeds and work without any credentials.

## Worker deployment

The now-playing strip is powered by a Cloudflare Worker. It auto-deploys via CI on every push to `main`. For first-time setup or manual redeploy:

```bash
cd worker
wrangler secret put LASTFM_API_KEY   # store key in Cloudflare (not GitHub Secrets)
wrangler deploy
```

The Worker URL (`now-playing.b-tonic.workers.dev`) is configured in `site.toml` under `[worker]` and is read by `build.py` to inject the correct endpoint into `index.html` at build time.

## Files

| File | Purpose |
|------|---------|
| `site.toml` | Site config — metadata, OG tags, analytics, and data source URLs. Read by `build.py` at build time. |
| `index.html` | The site. Contains comment markers (`<!-- tag:start/end -->`) where build.py injects content. |
| `style.css` | Styling. |
| `build.py` | Build script that fetches all data and updates index.html. |
| `CNAME` | Custom domain record (kept for reference; domain is configured in Cloudflare Pages dashboard). |
| `.github/workflows/build.yml` | GitHub Actions workflow for scheduled builds and deployment. |
