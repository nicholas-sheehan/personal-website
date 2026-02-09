#!/usr/bin/env python3
"""
Build script for nicsheehan.com

Fetches data from four sources and writes them into index.html:
  1. Gravatar profile (via REST API — no auth needed)
  2. Goodreads "currently reading" shelf (via RSS — no auth needed)
  3. Letterboxd recently watched films (via RSS — no auth needed)
  4. Instapaper starred/liked articles (via API — OAuth 1.0a)

Usage:
    python build.py              # full build
    python build.py auth         # one-time: exchange Instapaper credentials for OAuth tokens

Setup — Gravatar:
    Set GRAVATAR_USERNAME below to your Gravatar profile slug.
    Pulls display_name, job_title, company, location, and description.

Setup — Goodreads:
    Replace GOODREADS_RSS below with your RSS URL.
    Find it at: goodreads.com → My Books → Currently Reading → RSS link

Setup — Letterboxd:
    Replace LETTERBOXD_RSS below with your RSS URL.
    Find it at: letterboxd.com → your profile → RSS link

Setup — Instapaper:
    1. Request API credentials at https://www.instapaper.com/main/request_oauth_consumer_token
    2. Set INSTAPAPER_CONSUMER_KEY and INSTAPAPER_CONSUMER_SECRET as env vars
    3. Run:  python build.py auth
       This exchanges your username/password for OAuth tokens (stored in .instapaper_tokens)
       You only need to do this once.
    For CI, set all four INSTAPAPER_* values as environment variables/secrets.
"""

import base64
import hashlib
import hmac
import html
import json
import os
import re
import sys
import time
import urllib.parse
import urllib.request
import uuid
import xml.etree.ElementTree as ET

# ── Config ────────────────────────────────────────────────────────

GOODREADS_RSS = "https://www.goodreads.com/review/list_rss/175639385?shelf=currently-reading"

LETTERBOXD_RSS = "https://letterboxd.com/tonic2/rss/"
LETTERBOXD_LIMIT = 5  # recent films to show

GRAVATAR_USERNAME = "nicsheehanau"
GRAVATAR_API_KEY = os.environ.get("GRAVATAR_API_KEY", "")

INSTAPAPER_CONSUMER_KEY = os.environ.get("INSTAPAPER_CONSUMER_KEY", "YOUR_CONSUMER_KEY")
INSTAPAPER_CONSUMER_SECRET = os.environ.get("INSTAPAPER_CONSUMER_SECRET", "YOUR_CONSUMER_SECRET")
INSTAPAPER_TOKEN_FILE = ".instapaper_tokens"
INSTAPAPER_LIMIT = 5  # max articles to show

INDEX_PATH = "index.html"


# ══════════════════════════════════════════════════════════════════
#  Goodreads (RSS)
# ══════════════════════════════════════════════════════════════════

def fetch_goodreads(rss_url: str) -> list[dict]:
    """Return a list of {title, author} dicts from the RSS feed."""
    req = urllib.request.Request(rss_url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=15) as resp:
        tree = ET.parse(resp)

    books = []
    for item in tree.findall(".//item"):
        title_el = item.find("title")
        author_el = item.find("author_name")

        if title_el is None or title_el.text is None:
            continue

        title = title_el.text.strip()
        author = author_el.text.strip() if author_el is not None and author_el.text else "Unknown"
        books.append({"title": title, "author": author})

    return books


def build_book_html(books: list[dict]) -> str:
    """Turn a list of books into <li> elements."""
    if not books:
        return "          <li>Nothing at the moment — check back soon.</li>"
    lines = []
    for book in books:
        t = html.escape(book["title"])
        a = html.escape(book["author"])
        lines.append(f'          <li><em>{t}</em> — {a}</li>')
    return "\n".join(lines)


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
    """Turn a list of films into <li> elements."""
    if not films:
        return "          <li>Nothing at the moment — check back soon.</li>"
    lines = []
    for film in films:
        t = html.escape(film["title"])
        y = f' ({html.escape(film["year"])})' if film["year"] else ""
        stars = _star_rating(film["rating"])
        aria = f' aria-label="Rated {film["rating"]} out of 5"' if film["rating"] and stars else ""
        rating_span = f' <span class="stars"{aria}>{stars}</span>' if stars else ""
        lines.append(f'          <li><em>{t}</em>{y}{rating_span}</li>')
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


_ARROW_SVG = '<svg class="link-icon" xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M7 17l9.2-9.2M17 17V7H7"/></svg>'


def build_gravatar_links_html(profile: dict, email: str = "") -> str:
    """Build nav link buttons from Gravatar links + optional email."""
    links = profile.get("links", [])
    lines = []
    for link in links:
        label = html.escape(link["label"])
        url = html.escape(link["url"])
        lines.append(
            f'        <a href="{url}" class="link" target="_blank" rel="noopener noreferrer">\n'
            f'          <span class="link-label">{label}</span>\n'
            f'          {_ARROW_SVG}\n'
            f'        </a>'
        )
    if email:
        lines.append(
            f'        <a href="mailto:{html.escape(email)}" class="link">\n'
            f'          <span class="link-label">Email</span>\n'
            f'          {_ARROW_SVG}\n'
            f'        </a>'
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
            "url": item.get("url", "#"),
        })
    return articles


def build_article_html(articles: list[dict]) -> str:
    """Turn a list of articles into <li> elements with links."""
    if not articles:
        return "          <li>Nothing yet — check back soon.</li>"
    lines = []
    for article in articles:
        t = html.escape(article["title"])
        u = html.escape(article["url"])
        domain = urllib.parse.urlparse(article["url"]).hostname or ""
        domain = domain.removeprefix("www.")
        source = f' <span class="source">— {html.escape(domain)}</span>' if domain else ""
        lines.append(f'          <li><a href="{u}" target="_blank" rel="noopener noreferrer">{t}</a>{source}</li>')
    return "\n".join(lines)


# ══════════════════════════════════════════════════════════════════
#  HTML injection
# ══════════════════════════════════════════════════════════════════

def _make_pattern(tag: str) -> re.Pattern:
    return re.compile(
        rf"(<!-- {tag}:start -->)\n.*?\n(\s*<!-- {tag}:end -->)",
        re.DOTALL,
    )

GRAVATAR_LINKS_PATTERN = _make_pattern("gravatar-links")
GRAVATAR_AVATAR_PATTERN = _make_pattern("gravatar-avatar")
GRAVATAR_NAME_PATTERN = _make_pattern("gravatar-name")
GRAVATAR_TAGLINE_PATTERN = _make_pattern("gravatar-tagline")
GRAVATAR_BIO_PATTERN = _make_pattern("gravatar-bio")
GOODREADS_PATTERN = _make_pattern("goodreads")
LETTERBOXD_PATTERN = _make_pattern("letterboxd")
INSTAPAPER_PATTERN = _make_pattern("instapaper")


def inject(html_src: str, pattern: re.Pattern, new_content: str, label: str) -> str:
    """Replace content between start/end markers."""
    replacement = rf"\1\n{new_content}\n\2"
    result, count = pattern.subn(replacement, html_src)
    if count == 0:
        print(f"WARNING: Could not find <!-- {label}:start/end --> markers in index.html")
    return result


# ══════════════════════════════════════════════════════════════════
#  CLI
# ══════════════════════════════════════════════════════════════════

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

    # ── Gravatar ──
    print("Fetching Gravatar profile…")
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
    print(f"  Name: {name}, tagline: {tagline}, links: {len(profile.get('links', []))}")

    # ── Goodreads ──
    if "YOUR_USER_ID" in GOODREADS_RSS:
        print("⚠  Skipping Goodreads — update GOODREADS_RSS in build.py first.")
    else:
        print("Fetching Goodreads RSS…")
        books = fetch_goodreads(GOODREADS_RSS)
        print(f"  Found {len(books)} book(s) on currently-reading shelf.")
        src = inject(src, GOODREADS_PATTERN, build_book_html(books), "goodreads")

    # ── Letterboxd ──
    if "YOUR_USERNAME" in LETTERBOXD_RSS:
        print("⚠  Skipping Letterboxd — update LETTERBOXD_RSS in build.py first.")
    else:
        print("Fetching Letterboxd RSS…")
        films = fetch_letterboxd(LETTERBOXD_RSS, LETTERBOXD_LIMIT)
        print(f"  Found {len(films)} recent film(s).")
        src = inject(src, LETTERBOXD_PATTERN, build_film_html(films), "letterboxd")

    # ── Instapaper ──
    tokens = load_tokens()
    if INSTAPAPER_CONSUMER_KEY == "YOUR_CONSUMER_KEY":
        print("⚠  Skipping Instapaper — set your consumer key/secret in build.py first.")
    elif tokens is None:
        print("⚠  Skipping Instapaper — run 'python build.py auth' first.")
    else:
        print("Fetching Instapaper starred articles…")
        articles = fetch_instapaper_starred(tokens)
        print(f"  Found {len(articles)} starred article(s).")
        src = inject(src, INSTAPAPER_PATTERN, build_article_html(articles), "instapaper")

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
