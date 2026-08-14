# Trend Pipeline — Trend Intelligence & Content Enrichment System

Multi-source trend aggregation with intelligent enrichment — fetches trending topics
from Google Trends, NewsAPI, Mediastack, GNews, Currents, Reddit, RSS feeds, and 5 more news APIs (Webz.io, APITube, The News API, NYTimes, MediaCloud) - see .env.example for the keys,
deduplicates, scores, **enriches** each trend (category, growth, description, image,
related keywords/topics, SEO score), and serves everything via a REST API + live dashboard.

Built for **DigitalBrief** and **Jeet Digital Marketing Agency**.

---

## Recent Fixes (2026-08-13) — India RSS Feeds & Live News Channels

### 1. India news feeds integrated (10 new RSS sources)
- Added **BBC India, The Hindu, NDTV, India Today, Times of India, Indian Express,
  ThePrint, Hindustan Times, Business Standard, The Guardian India** to a structured
  `RSS_SOURCES` config (18 feeds total: 8 tech + 10 India) in `core/config.py`.
- RSS fetcher upgraded (`fetchers/rss.py`): browser User-Agent fetch + `feedparser.parse(string)`
  (fixes Business Standard 403-class blocks), per-item `publisher` attribution, image fallbacks
  (media_thumbnail → media_content → enclosure → itunes:image → first `<img>`), `updated_parsed`
  fallback, per-feed timeout, gentle 1s delay between feeds.
- New **India News** category rules (india/delhi/mumbai/kashmir/isro/lok sabha/rupee/sensex/
  bjp/ipl/bollywood …) + `india news` alias in `normalize_category()` — category filter now
  matches reliably.
- Aggregator recency tie-break: on equal scores, newer items surface first.
- 123+ RSS items per refresh → 130+ unique enriched trends; publishers shown as badges on cards.

### 2. Live News Channels section (13 channels)
- New **News Channels & Live News** section on the dashboard: 10 embeddable 24/7 live channels
  (NDTV, BBC News, Al Jazeera English, France 24, DW News, **WION**, **India Today**, Indian
  Express, News18, Euronews) + 3 official-site link cards (Sky News, Reuters, Times of India —
  embedding blocked/licensed, never bypassed).
- Embed pattern: `https://www.youtube-nocookie.com/embed/live_stream?channel=<UC-ID>&autoplay=1&mute=1`
  (privacy-enhanced, muted autoplay per browser policy) with "Watch on YouTube ↗" fallback.
- Channel IDs verified via YouTube RSS title check; `/api/channels` endpoint exposes the registry
  with sanitized URLs (http/https only, `UC\w{22}` ID validation).
- Channels are configurable from the `NEWS_CHANNELS` array (single edit point).

---

## Recent Fixes (2026-08-13) — Filtering, Refresh & Auto-Update

### 1. Category filtering made reliable
- **Root cause:** category values were compared with exact string equality; no
  normalization existed for case/whitespace/naming variants, and the filter UI
  state (active chip/select) was lost on every 60s data poll.
- **Fix:** new `normalize_category()` in `core/enrichment.py` (alias map +
  whitespace/case normalization) applied at enrichment time, at the API boundary
  (`_serialize_trend`), and in the `/api/trends/enriched` filter; frontend
  `normalizeCat()` mirrors the alias map; chips/select are deduped
  case-insensitively and the active filter is restored after every data update.
- Selecting any category now shows only matching news; **All Categories**
  restores the full feed; filters survive fetch/refresh/poll cycles.

### 2. Refresh button — full pipeline refresh
- **Root cause:** no concurrency guard (manual refresh could overlap the 30-min
  background loop), no request timeout (a slow pipeline left the button stuck),
  and a refresh yielding 0 trends called `cache.update([])` and wiped the feed.
- **Fix:** `asyncio.Lock` in `core/engine.py` serializes ALL pipeline runs
  (background loop, manual refresh, auto refresh); a 0-trend refresh now keeps
  the previous data and surfaces a visible error; frontend `refreshData()`
  guards double-clicks, times out after 90s, shows a loading state, and renders
  the latest cached data on failure — no browser reload needed.

### 3. Top Trending auto-update
- **Root cause:** the 60s poll only re-read the cache; new trends only arrived
  when the 30-min backend loop happened to run.
- **Fix:** central `AUTO_CFG` (POLL_MS / STALE_AFTER_S / REFRESH_URL) — the
  dashboard checks every 60s and triggers a real pipeline refresh when data is
  missing or older than 5 minutes, then re-renders hero + cards automatically.
  Manual and automatic refreshes share one guarded path, so they never conflict.

# Recent Fixes (2026-08-12)

1. **Real news now ranks first.** RSS feeds (real articles) carry the highest source
   weight (`40`); Google Trends topics are demoted (`12`) so real reporting leads the
   dashboard instead of search-term suggestions.
2. **No more Google Trends redirects.** Google Trends topics now link to **Google News**
   search (`news.google.com/search?q=…`) — real articles, never the `trends.google.com`
   explore page.
3. **Live current topics, not evergreen.** The Google Trends fetcher now uses Google's
   official **daily-trending RSS feed** (pytrends' "trending now" endpoints are
   deprecated and return 404), returning real-time topics like today's news and events.
4. **Factual descriptions only.** RSS descriptions are extracted from the real article
   summary (via `feedparser`); search topics get a clearly-labelled factual note — no
   fabricated or AI-generated news copy.

---

## Quick Start

```powershell
cd trend-pipeline
pip install -r requirements.txt
python api/index.py
```

Then open:
- **http://localhost:8765** — landing page
- **http://localhost:8765/dashboard** — enriched trend dashboard
- **http://localhost:8765/docs** — Swagger API docs

---

## Architecture

```
┌───────────────────────────────────────────────────────────────┐
│                      TREND PIPELINE                           │
├──────────┬──────────┬──────────┬──────────┬──────────────────┤
│ Google   │ NewsAPI  │ Reddit   │ RSS      │ Mediastack/GNews │
│ Trends   │          │          │ (8 feeds)│  /Currents       │
├──────────┴──────────┴──────────┴──────────┴──────────────────┤
│              Aggregator (merge → dedup → score → rank)       │
├───────────────────────────────────────────────────────────────┤
│         ENRICHMENT LAYER  (additive, non-breaking)           │
│   category · growth · description · image · keywords · SEO   │
├───────────────────────────────────────────────────────────────┤
│              Cache (in-memory + save/dismiss state)          │
├───────────────────────────────────────────────────────────────┤
│              REST API (FastAPI)                               │
│   /api/trends · /enriched · /article · /social · save/dismiss│
├───────────────────────────────────────────────────────────────┤
│              Dashboard (HTML, dark theme, responsive)         │
│   filters · sort · category · actions (Details/Article/Post) │
└───────────────────────────────────────────────────────────────┘
```

---

## Project Structure

| File | Purpose |
|------|---------|
| `api/index.py` | Unified entry point — pages + all REST API + actions |
| `core/engine.py` | Pipeline orchestrator — fetches, aggregates, enriches, caches |
| `core/aggregator.py` | Merge, deduplicate, score, rank + content ideas |
| `core/enrichment.py` | **NEW** — category, growth, description, image, keywords, SEO, article/social |
| `core/cache.py` | Thread-safe cache + save/dismiss state |
| `core/config.py` | All config — API keys, keywords, feeds, intervals |
| `fetchers/google_trends.py` | Real-time trending topics via Google's daily-trending RSS feed |
| `fetchers/rss.py` | Real articles + real description/image extraction |
| `dashboard.html` | Enriched dashboard UI |
| `landing.html` | SEO landing page |
| `static/favicon.svg` | Custom favicon |
| `vercel.json` / `.vercelignore` | Vercel deployment config |

---

## Enrichment Fields (per trend)

Every fetched trend is enriched with these **optional** fields (missing data is handled gracefully):

| Field | Description |
|-------|-------------|
| `category` | Auto-categorized (AI, Cybersecurity, Gadgets, Startups, …) |
| `growth_percentage` | Estimated growth (from real signal or score heuristic) |
| `description` | Concise factual description (30–80 words) |
| `image_url` / `image_source` / `image_license` | Category-themed featured image (SVG data URI) |
| `related_keywords` | Extracted for SEO/content |
| `related_topics` | Related subjects per category |
| `seo_score` | 0–100 content/SEO potential |
| `region` / `language` | Region and language metadata |
| `retrieved_at` | UTC timestamp |

### Content generation
- **Article brief** — meta title/description, target keywords, outline, FAQ
- **Social post** — hook, body, hashtags, CTA, image

---

## API Endpoints

| Endpoint | Description |
|----------|-------------|
| `GET /api/trends` | All trends (enriched). Filters: `?source=` `&min_score=` `&limit=` |
| `GET /api/trends/enriched` | Enriched trends. Sort: `?sort=score\|seo\|growth\|latest` + `?category=` |
| `GET /api/trends/top?n=10` | Top N trends |
| `GET /api/trends/ideas?min_score=50` | Content article ideas |
| `GET /api/trends/status` | Pipeline health + saved/dismissed counts |
| `GET /api/trends/refresh` | Force immediate refresh |
| `GET /api/trends/{rank}/article` | Generate article brief |
| `GET /api/trends/{rank}/social` | Generate social post |
| `POST /api/trends/{rank}/save` | Save a trend |
| `POST /api/trends/{rank}/dismiss` | Dismiss a trend |
| `GET /api/trends/saved` | List saved trends |

---

## API Keys

Set via `.env` (or environment variables). **All keys are optional** — the pipeline runs
with graceful fallbacks when they're missing.

| Service | Env var | Notes |
|---------|---------|-------|
| Mediastack | `MEDIASTACK_KEY` | News API |
| GNews | `GNEWS_KEY` | News API |
| Currents | `CURRENTS_KEY` | News API |
| NewsAPI | `NEWSAPI_KEY` | News headlines |
| Reddit | `REDDIT_CLIENT_ID` / `REDDIT_CLIENT_SECRET` | Script app |
| Webz.io (Lite) | `WEBZIO_API_KEY` | News API (throttled to 1 call/hour) |
| APITube | `APITUBE_API_KEY` | News API |
| The News API | `THENEWS_API_KEY` | News API |
| NYTimes | `NYT_API_KEY` (+ `NYT_APP_ID`) | Top Stories API |
| MediaCloud | `MEDIACLOUD_API_KEY` | Best-effort; endpoint unverified |

Google Trends + RSS feeds require no keys and always work.

---

## Scoring

`trend_score` (0–100): source weight + popularity signals + multi-source bonus.
`seo_score` (0–100): popularity (40) + real source URL (15) + description (15) +
title quality (15) + multi-source (15).

---

## Customization

- **Keywords** → `core/config.py` → `CONTENT_KEYWORDS`
- **RSS feeds** → `core/config.py` → `RSS_FEEDS`
- **Category rules** → `core/enrichment.py` → `CATEGORY_RULES`
- **Refresh interval** → `core/config.py` → `REFRESH_INTERVAL_MINUTES`

---

## Deployment

```powershell
# Local production
uvicorn api.index:app --host 0.0.0.0 --port 8765

# Vercel — entry point is api/index.py (see vercel.json)
```

---

## Backward Compatibility

The enrichment layer is **purely additive**. If it fails or is removed, trend
fetching, aggregation, and the dashboard continue working unchanged — all enrichment
fields are optional and have graceful fallbacks.
