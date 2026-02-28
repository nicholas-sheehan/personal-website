# Site Architecture

nicsheehan.com is a fully headless static site. All content is fetched from external services at build time — there is no CMS, no runtime server, no database.

## How it works

```mermaid
flowchart TD
    subgraph sources["External Sources — build time"]
        GV[Gravatar API]
        GR[Goodreads RSS]
        LB[Letterboxd RSS]
        IP[Instapaper API]
        LF[Last.fm API]
        TM[TMDB API]
    end

    subgraph local["Local Config"]
        ST[site.toml]
        CSS[style.css]
    end

    subgraph build["build.py"]
        BP[Fetch · Inject · Inline CSS\nGenerate OG image · Sitemap]
    end

    subgraph output["Output — committed to repo"]
        IH[index.html]
        OG[og-image.png]
        SM[sitemap.xml]
    end

    subgraph hosting["Hosting"]
        GHP[GitHub Pages\nwww.nicsheehan.com]
    end

    subgraph browser["Browser — runtime"]
        GF[Google Fonts CDN\nJetBrains Mono]
        GC[GoatCounter CDN\nAnalytics]
        JS[Inline JS\nBoot · Modal · Countdown · Snake]
    end

    sources --> build
    local --> build
    build --> output
    output --> hosting
    hosting --> browser
```

## Key decisions

- **No runtime server** — GitHub Pages serves static files only. Zero infrastructure to maintain.
- **Build-time content** — all external data is fetched by `build.py` and baked into `index.html`. The browser never calls any external data APIs.
- **Inline CSS** — `style.css` is inlined into `index.html` at build time, eliminating a render-blocking request.
- **Minimal JS** — no framework. Inline scripts only: boot sequence, item detail modal, countdown timer, Snake easter egg.
- **Graceful degradation** — all external fetches are wrapped in try/except. If a source fails, existing content is preserved and the build continues.
