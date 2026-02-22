#!/usr/bin/env python3
"""
Build script for nicsheehan.com

Fetches data from six sources and writes them into index.html:
  1. site.toml — site metadata, analytics, and data source config
  2. Gravatar profile (via REST API — GRAVATAR_API_KEY env var for full data)
  3. Goodreads "currently reading" and "read" shelves (via RSS — no auth needed)
  4. Letterboxd recently watched films (via RSS — no auth needed)
  5. Instapaper starred/liked articles (via API — OAuth 1.0a)
  6. Last.fm top tracks this month (via REST API — LASTFM_API_KEY env var)

Usage:
    python build.py              # full build
    python build.py auth         # one-time: exchange Instapaper credentials for OAuth tokens

Setup — site.toml:
    Edit site.toml to set title, description, URL, analytics ID, and feed URLs.
    This file is the single source of truth for all configuration.

Setup — Gravatar:
    Set sources.gravatar.username in site.toml to your Gravatar profile slug.
    Pulls display_name, job_title, company, location, and description.
    Set GRAVATAR_API_KEY env var for links and contact info (unauthenticated gives basic profile only).

Setup — Goodreads:
    Set sources.goodreads.currently_reading_rss and read_rss in site.toml.
    Find your RSS URLs at: goodreads.com → My Books → shelf → RSS link

Setup — Letterboxd:
    Set sources.letterboxd.rss in site.toml.
    Find it at: letterboxd.com → your profile → RSS link

Setup — Instapaper:
    1. Request API credentials at https://www.instapaper.com/main/request_oauth_consumer_token
    2. Set INSTAPAPER_CONSUMER_KEY and INSTAPAPER_CONSUMER_SECRET as env vars
    3. Run:  python build.py auth
       This exchanges your username/password for OAuth tokens (stored in .instapaper_tokens)
       You only need to do this once.
    For CI, set all four INSTAPAPER_* values as environment variables/secrets.

Setup — Last.fm:
    Set sources.lastfm.username in site.toml to your Last.fm username.
    Set LASTFM_API_KEY env var (get one at last.fm/api/account/create).
"""

import base64
from datetime import datetime, timedelta, timezone
import hashlib
import hmac
import html
import json
import os
import re
import sys
import time
try:
    import tomllib
except ModuleNotFoundError:
    import tomli as tomllib  # pip install tomli (for Python < 3.11)
import urllib.parse
import urllib.request
import uuid
import xml.etree.ElementTree as ET

# ── Config (from site.toml) ───────────────────────────────────────

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_CONFIG_PATH = os.path.join(_SCRIPT_DIR, "site.toml")

with open(_CONFIG_PATH, "rb") as _f:
    CONFIG = tomllib.load(_f)

SITE_URL = CONFIG["site"]["url"]

GOODREADS_RSS = CONFIG["sources"]["goodreads"]["currently_reading_rss"]
GOODREADS_READ_RSS = CONFIG["sources"]["goodreads"]["read_rss"]
GOODREADS_READ_LIMIT = CONFIG["sources"]["goodreads"]["read_limit"]

LETTERBOXD_RSS = CONFIG["sources"]["letterboxd"]["rss"]
LETTERBOXD_LIMIT = CONFIG["sources"]["letterboxd"]["limit"]

GRAVATAR_USERNAME = CONFIG["sources"]["gravatar"]["username"]
GRAVATAR_API_KEY = os.environ.get("GRAVATAR_API_KEY", "")

INSTAPAPER_CONSUMER_KEY = os.environ.get("INSTAPAPER_CONSUMER_KEY", "YOUR_CONSUMER_KEY")
INSTAPAPER_CONSUMER_SECRET = os.environ.get("INSTAPAPER_CONSUMER_SECRET", "YOUR_CONSUMER_SECRET")
INSTAPAPER_TOKEN_FILE = ".instapaper_tokens"
INSTAPAPER_LIMIT = CONFIG["sources"]["instapaper"]["limit"]
LASTFM_USERNAME = CONFIG["sources"]["lastfm"]["username"]
LASTFM_API_KEY = os.environ.get("LASTFM_API_KEY", "")
LASTFM_LIMIT = CONFIG["sources"]["lastfm"]["limit"]

INDEX_PATH = "index.html"
STYLE_PATH = "style.css"
OG_IMAGE_PATH = "og-image.png"
SITEMAP_PATH = "sitemap.xml"


# ══════════════════════════════════════════════════════════════════
#  Goodreads (RSS)
# ══════════════════════════════════════════════════════════════════

def fetch_goodreads(rss_url: str, limit: int = 0) -> list[dict]:
    """Return a list of {title, author, rating} dicts from the RSS feed."""
    req = urllib.request.Request(rss_url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=15) as resp:
        tree = ET.parse(resp)

    books = []
    for item in tree.findall(".//item"):
        title_el = item.find("title")
        author_el = item.find("author_name")
        rating_el = item.find("user_rating")

        if title_el is None or title_el.text is None:
            continue

        title = title_el.text.strip()
        author = author_el.text.strip() if author_el is not None and author_el.text else "Unknown"
        rating_text = rating_el.text.strip() if rating_el is not None and rating_el.text else "0"
        rating = min(int(rating_text), 5) if rating_text.isdigit() else 0
        books.append({"title": title, "author": author, "rating": rating})

        if limit and len(books) >= limit:
            break

    return books


def build_book_html(books: list[dict]) -> str:
    """Turn a list of books into panel-row divs."""
    if not books:
        return '                <div class="panel-row"><div class="row-content">Nothing at the moment — check back soon.</div></div>'
    lines = []
    for i, book in enumerate(books):
        t = html.escape(book["title"])
        a = html.escape(book["author"])
        rating = book.get("rating", 0)
        idx = f"{i + 1:02d}"
        if rating:
            aria = f' aria-label="Rated {rating} out of 5"'
            stars_html = f'\n                  <span class="row-meta book-stars"{aria}>{"★" * rating}</span>'
        else:
            stars_html = ""
        lines.append(
            f'                <div class="panel-row">\n'
            f'                  <span class="row-index">{idx}</span>\n'
            f'                  <div class="row-content">\n'
            f'                    <div class="book-title">{t}</div>\n'
            f'                    <div class="book-author">{a}</div>\n'
            f'                  </div>{stars_html}\n'
            f'                </div>'
        )
    return "\n".join(lines)


def build_now_reading_html(books: list[dict]) -> str:
    """Generate status strip HTML for currently-reading shelf.

    0 books  → placeholder comment (section invisible)
    1 book   → "Currently reading <em>Title</em> by Author"
    2+ books → "Currently reading <em>Title 1</em>, <em>Title 2</em>"
    """
    if not books:
        return "            <!-- no books currently reading -->"
    if len(books) == 1:
        t = html.escape(books[0]["title"])
        a = html.escape(books[0]["author"])
        text = f"Currently reading <em>{t}</em> by {a}"
    else:
        titles = ", ".join(f"<em>{html.escape(b['title'])}</em>" for b in books)
        text = f"Currently reading {titles}"
    return (
        '            <div class="status-strip">\n'
        '              <span class="status-strip-label">Now reading</span>\n'
        '              <span class="status-strip-sep">›</span>\n'
        f'              <span class="status-strip-text">{text}</span>\n'
        '            </div>'
    )


# ══════════════════════════════════════════════════════════════════
#  Letterboxd (RSS)
# ══════════════════════════════════════════════════════════════════

LETTERBOXD_NS = {"letterboxd": "https://letterboxd.com"}


def fetch_letterboxd(rss_url: str, limit: int) -> list[dict]:
    """Return a list of {title, year, rating, url} dicts from the RSS feed."""
    req = urllib.request.Request(rss_url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=15) as resp:
        tree = ET.parse(resp)

    films = []
    for item in tree.findall(".//item"):
        # Skip non-film entries (e.g. list updates)
        film_title = item.find("letterboxd:filmTitle", LETTERBOXD_NS)
        if film_title is None or film_title.text is None:
            continue

        title = film_title.text.strip()

        year_el = item.find("letterboxd:filmYear", LETTERBOXD_NS)
        year = year_el.text.strip() if year_el is not None and year_el.text else ""

        rating_el = item.find("letterboxd:memberRating", LETTERBOXD_NS)
        rating = float(rating_el.text) if rating_el is not None and rating_el.text else None

        link_el = item.find("link")
        url = link_el.text.strip() if link_el is not None and link_el.text else "#"

        films.append({"title": title, "year": year, "rating": rating, "url": url})

        if len(films) >= limit:
            break

    return films


def _star_rating(rating: float) -> str:
    """Convert a numeric rating (0.5–5.0) to star characters."""
    if rating is None:
        return ""
    full = int(rating)
    half = rating % 1 >= 0.5
    return "★" * full + ("½" if half else "")


def build_film_html(films: list[dict]) -> str:
    """Turn a list of films into panel-row divs."""
    if not films:
        return '                <div class="panel-row"><div class="row-content">Nothing at the moment — check back soon.</div></div>'
    lines = []
    for i, film in enumerate(films):
        t = html.escape(film["title"])
        y = html.escape(film["year"]) if film["year"] else ""
        stars = _star_rating(film["rating"])
        idx = f"{i + 1:02d}"
        if stars:
            aria = f' aria-label="Rated {film["rating"]} out of 5"'
            stars_html = f'\n                  <span class="row-meta film-stars"{aria}>{stars}</span>'
        else:
            stars_html = ""
        lines.append(
            f'                <div class="panel-row">\n'
            f'                  <span class="row-index">{idx}</span>\n'
            f'                  <div class="row-content">\n'
            f'                    <div class="film-title">{t}</div>\n'
            f'                    <div class="film-year">{y}</div>\n'
            f'                  </div>{stars_html}\n'
            f'                </div>'
        )
    return "\n".join(lines)


# ══════════════════════════════════════════════════════════════════
#  Gravatar (REST API)
# ══════════════════════════════════════════════════════════════════

def fetch_gravatar(username: str, api_key: str = "") -> dict:
    """Fetch profile data from Gravatar API."""
    url = f"https://api.gravatar.com/v3/profiles/{username}"
    headers = {"Accept": "application/json"}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=15) as resp:
        return json.loads(resp.read().decode())


def build_gravatar_tagline(profile: dict) -> str:
    """Build a tagline from job_title, company, and location."""
    parts = []
    if profile.get("job_title"):
        title = profile["job_title"]
        if profile.get("company"):
            title += f' at {profile["company"]}'
        parts.append(title)
    if profile.get("location"):
        parts.append(profile["location"])
    return " · ".join(parts) if parts else ""


def _norm_url(url: str) -> str:
    """Normalise a URL for deduplication by stripping trailing slashes."""
    return url.rstrip("/")


def build_jsonld(profile: dict, site_url: str) -> str:
    """Build a JSON-LD Person schema from Gravatar profile data."""
    data = {
        "@context": "https://schema.org",
        "@type": "Person",
        "name": profile.get("display_name", ""),
        "url": site_url,
    }
    if profile.get("job_title"):
        data["jobTitle"] = profile["job_title"]
    if profile.get("company"):
        data["worksFor"] = {"@type": "Organization", "name": profile["company"]}
    if profile.get("location"):
        data["homeLocation"] = {"@type": "Place", "name": profile["location"]}
    if profile.get("description"):
        data["description"] = profile["description"]
    if profile.get("avatar_url"):
        data["image"] = profile["avatar_url"]
    seen: set[str] = set()
    same_as: list[str] = []

    def _add(url: str) -> None:
        key = _norm_url(url)
        if key not in seen:
            seen.add(key)
            same_as.append(url)

    _add(profile["profile_url"])
    for link in profile.get("links", []):
        if link.get("url"):
            _add(link["url"])
    for acct in profile.get("verified_accounts", []):
        if acct.get("url"):
            _add(acct["url"])
    data["sameAs"] = same_as
    return json.dumps(data, indent=2)


def generate_og_image(profile: dict, output_path: str):
    """Generate a 1200x630 OG image with avatar, name, and tagline."""
    try:
        from PIL import Image, ImageDraw, ImageFont
        import io
    except ImportError:
        print("  ⚠  Pillow not installed — skipping OG image generation.")
        return False

    WIDTH, HEIGHT = 1200, 630
    BG_COLOR = (10, 10, 10)  # #0a0a0a
    TEXT_PRIMARY = (229, 229, 229)  # #e5e5e5
    TEXT_SECONDARY = (163, 163, 163)  # #a3a3a3
    ACCENT = (59, 130, 246)  # #3b82f6

    img = Image.new("RGB", (WIDTH, HEIGHT), BG_COLOR)
    draw = ImageDraw.Draw(img)

    # Load fonts — try common paths, fall back to default
    def load_font(size, bold=False):
        paths = [
            # macOS
            "/System/Library/Fonts/Helvetica.ttc",
            "/System/Library/Fonts/SFNSText.ttf",
            # Ubuntu/GitHub Actions
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold
            else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        ]
        for p in paths:
            try:
                return ImageFont.truetype(p, size)
            except (OSError, IOError):
                continue
        return ImageFont.load_default()

    font_name = load_font(54, bold=True)
    font_tagline = load_font(24)

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
            cx, cy = avatar_x + avatar_size // 2, avatar_y + avatar_size // 2
            draw.ellipse(
                (cx - ring_r, cy - ring_r, cx + ring_r, cy + ring_r),
                outline=ACCENT, width=3,
            )

            img.paste(avatar, (avatar_x, avatar_y), mask)
        except Exception as e:
            print(f"  ⚠  Could not download avatar: {e}")

    # Draw text
    text_x = avatar_x + avatar_size + 60
    name = profile.get("display_name", "")
    tagline = build_gravatar_tagline(profile)

    name_y = HEIGHT // 2 - 40
    draw.text((text_x, name_y), name, fill=TEXT_PRIMARY, font=font_name)

    if tagline:
        tagline_y = name_y + 70
        draw.text((text_x, tagline_y), tagline, fill=TEXT_SECONDARY, font=font_tagline)

    img.save(output_path, "PNG", optimize=True)
    return True


_NAV_EXCLUDED_DOMAINS = frozenset({"goodreads.com", "letterboxd.com"})


def build_gravatar_links_html(profile: dict, email: str = "") -> str:
    """Build nav link buttons from Gravatar links + optional email.
    Excludes Goodreads and Letterboxd — they have contextual panel footer links instead.
    """
    links = profile.get("links", [])
    lines = []
    for link in links:
        url = link.get("url", "")
        domain = urllib.parse.urlparse(url).hostname or ""
        domain = domain.removeprefix("www.")
        if domain in _NAV_EXCLUDED_DOMAINS:
            continue
        label = html.escape(link["label"])
        url_esc = html.escape(url)
        lines.append(
            f'                <a href="{url_esc}" class="system-nav-link" target="_blank" rel="noopener noreferrer">{label}</a>'
        )
    if email:
        lines.append(
            f'                <a href="mailto:{html.escape(email)}" class="system-nav-link">Email</a>'
        )
    return "\n".join(lines)


# ══════════════════════════════════════════════════════════════════
#  Instapaper (OAuth 1.0a / xAuth)
# ══════════════════════════════════════════════════════════════════

INSTAPAPER_API = "https://www.instapaper.com"


def _oauth_sign(method: str, url: str, params: dict,
                consumer_secret: str, token_secret: str = "") -> str:
    """Generate an OAuth 1.0a HMAC-SHA1 signature."""
    sorted_params = urllib.parse.urlencode(sorted(params.items()))
    base_string = "&".join([
        method.upper(),
        urllib.parse.quote(url, safe=""),
        urllib.parse.quote(sorted_params, safe=""),
    ])
    signing_key = f"{urllib.parse.quote(consumer_secret, safe='')}&{urllib.parse.quote(token_secret, safe='')}"
    sig = hmac.new(signing_key.encode(), base_string.encode(), hashlib.sha1)
    return base64.b64encode(sig.digest()).decode()


def _oauth_headers(url: str, consumer_key: str, consumer_secret: str,
                   token: str = "", token_secret: str = "",
                   extra_params: dict = None) -> dict:
    """Build an Authorization header for an OAuth 1.0a request."""
    oauth_params = {
        "oauth_consumer_key": consumer_key,
        "oauth_nonce": uuid.uuid4().hex,
        "oauth_signature_method": "HMAC-SHA1",
        "oauth_timestamp": str(int(time.time())),
        "oauth_version": "1.0",
    }
    if token:
        oauth_params["oauth_token"] = token

    all_params = {**oauth_params, **(extra_params or {})}
    signature = _oauth_sign("POST", url, all_params, consumer_secret, token_secret)
    oauth_params["oauth_signature"] = signature

    auth_str = ", ".join(
        f'{urllib.parse.quote(k, safe="")}="{urllib.parse.quote(v, safe="")}"'
        for k, v in sorted(oauth_params.items())
    )
    return {"Authorization": f"OAuth {auth_str}"}


def instapaper_auth(username: str, password: str) -> dict:
    """Exchange username/password for OAuth tokens via xAuth."""
    url = f"{INSTAPAPER_API}/api/1.1/oauth/access_token"
    body_params = {
        "x_auth_username": username,
        "x_auth_password": password,
        "x_auth_mode": "client_auth",
    }
    headers = _oauth_headers(
        url, INSTAPAPER_CONSUMER_KEY, INSTAPAPER_CONSUMER_SECRET,
        extra_params=body_params,
    )
    body = urllib.parse.urlencode(body_params).encode()
    req = urllib.request.Request(url, data=body, headers=headers, method="POST")
    with urllib.request.urlopen(req, timeout=15) as resp:
        result = urllib.parse.parse_qs(resp.read().decode())

    tokens = {
        "oauth_token": result["oauth_token"][0],
        "oauth_token_secret": result["oauth_token_secret"][0],
    }
    return tokens


def save_tokens(tokens: dict):
    """Save OAuth tokens to a local file."""
    with open(INSTAPAPER_TOKEN_FILE, "w") as f:
        json.dump(tokens, f)
    print(f"  Tokens saved to {INSTAPAPER_TOKEN_FILE}")
    print(f"  ⚠  Add {INSTAPAPER_TOKEN_FILE} to .gitignore — it contains secrets.")


def load_tokens() -> dict:
    """Load OAuth tokens from env vars (CI) or local file."""
    env_token = os.environ.get("INSTAPAPER_OAUTH_TOKEN")
    env_secret = os.environ.get("INSTAPAPER_OAUTH_TOKEN_SECRET")
    if env_token and env_secret:
        return {"oauth_token": env_token, "oauth_token_secret": env_secret}
    if not os.path.exists(INSTAPAPER_TOKEN_FILE):
        return None
    with open(INSTAPAPER_TOKEN_FILE, "r") as f:
        return json.load(f)

_TRACKING_PARAMS = frozenset({
    "utm_source", "utm_medium", "utm_campaign", "utm_content", "utm_term", "utm_id",
    "fbclid", "gclid", "mc_cid", "mc_eid",
})


def _strip_tracking_params(url: str) -> str:
    """Remove common URL tracking parameters from a URL."""
    parsed = urllib.parse.urlparse(url)
    if not parsed.scheme:
        return url
    qs = urllib.parse.parse_qs(parsed.query, keep_blank_values=True)
    clean_qs = {k: v for k, v in qs.items() if k.lower() not in _TRACKING_PARAMS}
    clean_query = urllib.parse.urlencode(clean_qs, doseq=True)
    return urllib.parse.urlunparse(parsed._replace(query=clean_query))



def fetch_instapaper_starred(tokens: dict) -> list[dict]:
    """Fetch starred bookmarks from Instapaper."""
    url = f"{INSTAPAPER_API}/api/1.1/bookmarks/list"
    body_params = {
        "folder_id": "starred",
        "limit": str(INSTAPAPER_LIMIT),
    }
    headers = _oauth_headers(
        url, INSTAPAPER_CONSUMER_KEY, INSTAPAPER_CONSUMER_SECRET,
        token=tokens["oauth_token"], token_secret=tokens["oauth_token_secret"],
        extra_params=body_params,
    )
    body = urllib.parse.urlencode(body_params).encode()
    req = urllib.request.Request(url, data=body, headers=headers, method="POST")
    with urllib.request.urlopen(req, timeout=15) as resp:
        data = json.loads(resp.read().decode())

    bookmarks = data.get("bookmarks", data) if isinstance(data, dict) else data
    articles = []
    for item in bookmarks:
        if not isinstance(item, dict) or item.get("type") != "bookmark":
            continue
        articles.append({
            "title": item.get("title", "Untitled"),
            "url": _strip_tracking_params(item.get("url", "#")),
        })
    return articles


def build_article_html(articles: list[dict]) -> str:
    """Turn a list of articles into panel-row divs with links."""
    if not articles:
        return '                <div class="panel-row"><div class="row-content">Nothing yet — check back soon.</div></div>'
    lines = []
    for i, article in enumerate(articles):
        t = html.escape(article["title"])
        u = html.escape(article["url"])
        domain = urllib.parse.urlparse(article["url"]).hostname or ""
        domain = domain.removeprefix("www.")
        source_html = f'\n                          <span class="article-source">{html.escape(domain)}</span>' if domain else ""
        idx = f"{i + 1:02d}"
        lines.append(
            f'                <div class="panel-row">\n'
            f'                  <span class="row-index">{idx}</span>\n'
            f'                  <div class="row-content">\n'
            f'                    <a href="{u}" target="_blank" rel="noopener noreferrer">\n'
            f'                      <div class="article-row-inner">\n'
            f'                        <div>\n'
            f'                          <div class="article-title">{t}</div>{source_html}\n'
            f'                        </div>\n'
            f'                      </div>\n'
            f'                    </a>\n'
            f'                  </div>\n'
            f'                </div>'
        )
    return "\n".join(lines)



# ══════════════════════════════════════════════════════════════════
#  Last.fm (REST API)
# ══════════════════════════════════════════════════════════════════

LASTFM_API = "https://ws.audioscrobbler.com/2.0/"


def fetch_lastfm_top_tracks(username: str, api_key: str, limit: int) -> list[dict]:
    """Return a list of {title, artist, plays} dicts from Last.fm top tracks."""
    params = urllib.parse.urlencode({
        "method": "user.getTopTracks",
        "user": username,
        "period": "1month",
        "limit": str(limit),
        "api_key": api_key,
        "format": "json",
    })
    url = f"{LASTFM_API}?{params}"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=15) as resp:
        data = json.loads(resp.read().decode())

    tracks = []
    for track in data.get("toptracks", {}).get("track", []):
        tracks.append({
            "title": track.get("name", ""),
            "artist": track.get("artist", {}).get("name", ""),
            "plays": int(track.get("playcount", 0) or 0),
        })
    return tracks


def build_music_html(tracks: list[dict]) -> str:
    """Turn a list of tracks into panel-row divs."""
    if not tracks:
        return '                <div class="panel-row"><div class="row-content">Nothing at the moment — check back soon.</div></div>'
    lines = []
    for i, track in enumerate(tracks):
        t = html.escape(track["title"])
        a = html.escape(track["artist"])
        p = track["plays"]
        play_word = "play" if p == 1 else "plays"
        idx = f"{i + 1:02d}"
        lines.append(
            f'                <div class="panel-row">\n'
            f'                  <span class="row-index">{idx}</span>\n'
            f'                  <div class="row-content">\n'
            f'                    <div class="track-title">{t}</div>\n'
            f'                    <div class="track-artist">{a}</div>\n'
            f'                  </div>\n'
            f'                  <span class="row-meta"><span class="play-count">{p} {play_word}</span></span>\n'
            f'                </div>'
        )
    return "\n".join(lines)


# ══════════════════════════════════════════════════════════════════
#  Meta & analytics (from TOML config)
# ══════════════════════════════════════════════════════════════════

def build_meta_html(config: dict) -> str:
    """Generate meta tags block from TOML config."""
    site = config["site"]
    social = config["social"]
    url = site["url"]
    og_image = f"{url}/og-image.png"
    lines = [
        f'  <title>{html.escape(site["title"])}</title>',
        f'  <meta name="description" content="{html.escape(site["description"])}">',
        f'  <link rel="canonical" href="{html.escape(url)}/">',
        f'  <meta property="og:title" content="{html.escape(site["title"])}">',
        f'  <meta property="og:description" content="{html.escape(site["description"])}">',
        f'  <meta property="og:image" content="{html.escape(og_image)}">',
        f'  <meta property="og:type" content="{html.escape(social["og_type"])}">',
        f'  <meta property="og:url" content="{html.escape(url)}/">',
    ]
    return "\n".join(lines)


def build_analytics_html(config: dict) -> str:
    """Generate analytics script tag from TOML config."""
    gc = html.escape(config["analytics"]["goatcounter"])
    return f'  <script data-goatcounter="https://{gc}.goatcounter.com/count" async src="//gc.zgo.at/count.js"></script>'


# ══════════════════════════════════════════════════════════════════
#  HTML injection
# ══════════════════════════════════════════════════════════════════

def _make_pattern(tag: str) -> re.Pattern:
    return re.compile(
        rf"(<!-- {tag}:start -->)\n.*?\n(\s*<!-- {tag}:end -->)",
        re.DOTALL,
    )

META_PATTERN = _make_pattern("meta")
ANALYTICS_PATTERN = _make_pattern("analytics")
JSONLD_PATTERN = _make_pattern("jsonld")
GRAVATAR_LINKS_PATTERN = _make_pattern("gravatar-links")
GRAVATAR_AVATAR_PATTERN = _make_pattern("gravatar-avatar")
GRAVATAR_NAME_PATTERN = _make_pattern("gravatar-name")
GRAVATAR_TAGLINE_PATTERN = _make_pattern("gravatar-tagline")
GRAVATAR_BIO_PATTERN = _make_pattern("gravatar-bio")
GOODREADS_PATTERN = _make_pattern("goodreads")
GOODREADS_NOW_PATTERN = _make_pattern("goodreads-now")
GOODREADS_READ_PATTERN = _make_pattern("goodreads-read")
LETTERBOXD_PATTERN = _make_pattern("letterboxd")
INSTAPAPER_PATTERN = _make_pattern("instapaper")
MUSIC_PATTERN = _make_pattern("music")
UPDATED_PATTERN = _make_pattern("updated")
STYLE_PATTERN = _make_pattern("style")


def inject(html_src: str, pattern: re.Pattern, new_content: str, label: str) -> str:
    """Replace content between start/end markers."""
    replacement = rf"\1\n{new_content}\n\2"
    result, count = pattern.subn(replacement, html_src)
    if count == 0:
        print(f"WARNING: Could not find <!-- {label}:start/end --> markers in index.html")
    return result


def update_sitemap(path: str, last_mod: datetime) -> None:
    """Write lastmod date into sitemap.xml."""
    lastmod_str = last_mod.strftime("%Y-%m-%d")
    content = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        '  <url>\n'
        f'    <loc>{SITE_URL}/</loc>\n'
        f'    <lastmod>{lastmod_str}</lastmod>\n'
        '    <changefreq>daily</changefreq>\n'
        '  </url>\n'
        '</urlset>\n'
    )
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"  Updated {path} with lastmod {lastmod_str}")


# ══════════════════════════════════════════════════════════════════
#  CLI
# ══════════════════════════════════════════════════════════════════

def _next_build_utc(now: datetime) -> datetime:
    """Return the next scheduled 22:00 UTC build time strictly after now."""
    today_build = now.replace(hour=22, minute=0, second=0, microsecond=0)
    if now < today_build:
        return today_build
    return today_build + timedelta(days=1)


def cmd_auth():
    """Interactive: exchange Instapaper credentials for tokens."""
    if INSTAPAPER_CONSUMER_KEY == "YOUR_CONSUMER_KEY":
        print("⚠  Set INSTAPAPER_CONSUMER_KEY and INSTAPAPER_CONSUMER_SECRET in build.py first.")
        sys.exit(1)

    import getpass
    print("Instapaper authentication (xAuth)")
    print("Your password is sent directly to Instapaper over HTTPS")
    print("and is NOT stored — only the resulting tokens are saved.\n")
    username = input("Instapaper email: ")
    password = getpass.getpass("Instapaper password (blank if none): ")

    print("Exchanging credentials…")
    tokens = instapaper_auth(username, password)
    save_tokens(tokens)
    print("Done ✓")


def cmd_build():
    """Main build: fetch both sources and update index.html."""
    with open(INDEX_PATH, "r", encoding="utf-8") as f:
        src = f.read()

    # ── <html lang> (from site.toml) ──
    lang = CONFIG["site"].get("lang", "en")
    src = re.sub(r'<html\b[^>]*>', f'<html lang="{html.escape(lang)}">', src, count=1)
    print(f"  Injecting lang={lang}\u2026")

    # ── Meta tags (from site.toml) ──
    print("Injecting meta tags from site.toml…")
    src = inject(src, META_PATTERN, build_meta_html(CONFIG), "meta")

    # ── Analytics (from site.toml) ──
    print("Injecting analytics from site.toml…")
    src = inject(src, ANALYTICS_PATTERN, build_analytics_html(CONFIG), "analytics")

    # ── Gravatar ──
    print("Fetching Gravatar profile…")
    try:
        profile = fetch_gravatar(GRAVATAR_USERNAME, GRAVATAR_API_KEY)
        name = html.escape(profile.get("display_name", ""))
        tagline = html.escape(build_gravatar_tagline(profile))
        bio = profile.get("description", "")
        avatar_url = profile.get("avatar_url", "")
        if avatar_url:
            avatar_html = f'        <img class="avatar" src="{html.escape(avatar_url)}?s=192" alt="{name}" width="96" height="96">'
            src = inject(src, GRAVATAR_AVATAR_PATTERN, avatar_html, "gravatar-avatar")
        if name:
            src = inject(src, GRAVATAR_NAME_PATTERN, f"        {name}", "gravatar-name")
        if tagline:
            src = inject(src, GRAVATAR_TAGLINE_PATTERN, f"        {tagline}", "gravatar-tagline")
        if bio:
            bio_html = f"        <p>{html.escape(bio)}</p>"
            src = inject(src, GRAVATAR_BIO_PATTERN, bio_html, "gravatar-bio")
        contact_email = profile.get("contact_info", {}).get("email", "")
        links_html = build_gravatar_links_html(profile, email=contact_email)
        if links_html:
            src = inject(src, GRAVATAR_LINKS_PATTERN, links_html, "gravatar-links")
        jsonld = build_jsonld(profile, SITE_URL)
        src = inject(src, JSONLD_PATTERN, f"    <script type=\"application/ld+json\">\n{jsonld}\n    </script>", "jsonld")
        print(f"  Name: {name}, tagline: {tagline}, links: {len(profile.get('links', []))}")

        # ── OG image ──
        print("Generating OG image…")
        if generate_og_image(profile, OG_IMAGE_PATH):
            print(f"  Saved {OG_IMAGE_PATH}")
    except Exception as e:
        print(f"  ⚠  Gravatar fetch failed: {e} — keeping existing content")

    # ── Goodreads ──
    if "YOUR_USER_ID" in GOODREADS_RSS:
        print("⚠  Skipping Goodreads — update sources.goodreads in site.toml first.")
    else:
        print("Fetching Goodreads RSS…")
        try:
            books = fetch_goodreads(GOODREADS_RSS)
            print(f"  Found {len(books)} book(s) on currently-reading shelf.")
            src = inject(src, GOODREADS_PATTERN, build_book_html(books), "goodreads")
            src = inject(src, GOODREADS_NOW_PATTERN, build_now_reading_html(books), "goodreads-now")

            print("Fetching Goodreads read shelf…")
            read_books = fetch_goodreads(GOODREADS_READ_RSS, limit=GOODREADS_READ_LIMIT)
            print(f"  Found {len(read_books)} book(s) on read shelf.")
            src = inject(src, GOODREADS_READ_PATTERN, build_book_html(read_books), "goodreads-read")
        except Exception as e:
            print(f"  ⚠  Goodreads fetch failed: {e} — keeping existing content")

    # ── Letterboxd ──
    if "YOUR_USERNAME" in LETTERBOXD_RSS:
        print("⚠  Skipping Letterboxd — update sources.letterboxd in site.toml first.")
    else:
        print("Fetching Letterboxd RSS…")
        try:
            films = fetch_letterboxd(LETTERBOXD_RSS, LETTERBOXD_LIMIT)
            print(f"  Found {len(films)} recent film(s).")
            src = inject(src, LETTERBOXD_PATTERN, build_film_html(films), "letterboxd")
        except Exception as e:
            print(f"  ⚠  Letterboxd fetch failed: {e} — keeping existing content")

    # ── Instapaper ──
    tokens = load_tokens()
    if INSTAPAPER_CONSUMER_KEY == "YOUR_CONSUMER_KEY":
        print("⚠  Skipping Instapaper — set INSTAPAPER_CONSUMER_KEY env var first.")
    elif tokens is None:
        print("⚠  Skipping Instapaper — run 'python build.py auth' first.")
    else:
        print("Fetching Instapaper starred articles…")
        try:
            articles = fetch_instapaper_starred(tokens)
            print(f"  Found {len(articles)} starred article(s).")
            src = inject(src, INSTAPAPER_PATTERN, build_article_html(articles), "instapaper")
        except Exception as e:
            print(f"  ⚠  Instapaper fetch failed: {e} — keeping existing content")

    # ── Last.fm ──
    if not LASTFM_API_KEY:
        print("⚠  Skipping Last.fm — set LASTFM_API_KEY env var first.")
    else:
        print("Fetching Last.fm top tracks…")
        try:
            tracks = fetch_lastfm_top_tracks(LASTFM_USERNAME, LASTFM_API_KEY, LASTFM_LIMIT)
            print(f"  Found {len(tracks)} top track(s).")
            src = inject(src, MUSIC_PATTERN, build_music_html(tracks), "music")
        except Exception as e:
            print(f"  ⚠  Last.fm fetch failed: {e} — keeping existing content")

    # ── Inline CSS ──
    if os.path.exists(STYLE_PATH):
        print("Inlining style.css…")
        with open(STYLE_PATH, "r", encoding="utf-8") as f:
            css = f.read()
        style_html = f"  <style>\n{css}  </style>"
        src = inject(src, STYLE_PATTERN, style_html, "style")

    # ── Last build timestamp + countdown ──
    now = datetime.now(timezone.utc)
    next_build = _next_build_utc(now)
    next_iso = next_build.strftime("%Y-%m-%dT%H:%M:%SZ")
    built_iso = now.strftime("%Y-%m-%dT%H:%M:%SZ")
    updated_str = now.strftime("%-d %b %Y at %H:%M UTC")
    updated_html = (
        f'            <p class="colophon-timestamp">'
        f'<span class="pulse-dot" aria-hidden="true"></span>'
        f' Last build: <span class="colophon-buildtime" data-built="{built_iso}">{updated_str}</span>'
        f'<span class="next-update" data-next="{next_iso}"></span>'
        f'</p>'
    )
    src = inject(src, UPDATED_PATTERN, updated_html, "updated")
    print(f"  Timestamp: {updated_str} · next build: {next_iso}")

    # ── Sitemap ──
    update_sitemap(SITEMAP_PATH, now)

    # ── Write ──
    with open(INDEX_PATH, "w", encoding="utf-8") as f:
        f.write(src)

    print(f"Updated {INDEX_PATH} ✓")


def main():
    if len(sys.argv) > 1 and sys.argv[1] == "auth":
        cmd_auth()
    else:
        cmd_build()


if __name__ == "__main__":
    main()
