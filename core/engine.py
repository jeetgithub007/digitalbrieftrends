"""Pipeline engine — orchestrates all fetchers."""
import asyncio, logging, aiohttp
from core.config import *
from core.cache import cache
from core.aggregator import TrendAggregator
from fetchers.mediastack import fetch_mediastack
from fetchers.gnews import fetch_gnews
from fetchers.currents import fetch_currents
from fetchers.rss import fetch_rss
from fetchers.google_trends import fetch_google_trends
from fetchers.webzio import fetch_webzio
from fetchers.apitube import fetch_apitube
from fetchers.thenewsapi import fetch_thenewsapi
from fetchers.nytimes import fetch_nytimes
from fetchers.mediacloud import fetch_mediacloud

logger = logging.getLogger("trends.engine")
aggregator = TrendAggregator(TREND_SCORE_WEIGHTS, MULTI_SOURCE_BONUS, MAX_TRENDS)


import re as _re


def _sanitize_err(e):
    """Strip URLs (and any query-string API keys) from error text before it
    can reach logs or the dashboard's 'recent errors' list."""
    return _re.sub(r"https?://\S+", "<url>", str(e))[:200]


# Serializes all pipeline runs (background loop, manual refresh, auto refresh)
# so concurrent refreshes can never overlap or race the cache.
_pipeline_lock = asyncio.Lock()


async def run_pipeline():
    async with _pipeline_lock:
        return await _run_pipeline_locked()


async def _run_pipeline_locked():
    logger.info("=" * 50)
    logger.info("Pipeline started (12 sources)")
    sources = {}

    async with aiohttp.ClientSession() as session:
        async def safe(name, coro):
            try:
                return name, await coro
            except Exception as e:
                logger.error(f"{name}: {_sanitize_err(e)}")
                cache.add_error(f"{name}: {_sanitize_err(e)}")
                return name, []

        tasks = [
            safe("mediastack", fetch_mediastack(session, MEDIASTACK_KEY, MEDIASTACK_LIMIT)),
            safe("gnews", fetch_gnews(session, GNEWS_KEY, GNEWS_LIMIT)),
            safe("currents", fetch_currents(session, CURRENTS_KEY, CURRENTS_LIMIT)),
            safe("rss", fetch_rss(RSS_FEEDS)),
            safe("webzio", fetch_webzio(session, WEBZIO_API_KEY, WEBZIO_LIMIT, WEBZIO_TIMEOUT)),
            safe("apitube", fetch_apitube(session, APITUBE_API_KEY, APITUBE_LIMIT, APITUBE_TIMEOUT)),
            safe("thenewsapi", fetch_thenewsapi(session, THENEWS_API_KEY, THENEWS_LIMIT, THENEWS_TIMEOUT)),
            safe("nytimes", fetch_nytimes(session, NYT_API_KEY, NYT_LIMIT, NYT_TIMEOUT, NYT_APP_ID)),
            safe("mediacloud", fetch_mediacloud(session, MEDIACLOUD_API_KEY, MEDIACLOUD_LIMIT, MEDIACLOUD_TIMEOUT)),
        ]
        for name, data in await asyncio.wait_for(asyncio.gather(*tasks), timeout=90):
            sources[name] = data
            logger.info(f"  {name}: {len(data)} items")

        # NewsAPI
        if NEWSAPI_KEY:
            try:
                params = {"country": "in", "category": "technology", "apiKey": NEWSAPI_KEY, "pageSize": 15}
                async with session.get("https://newsapi.org/v2/top-headlines", params=params) as r:
                    if r.status == 200:
                        data = await r.json()
                        sources["newsapi"] = [{"title": a["title"], "url": a.get("url", ""),
                                               "source": a.get("source", {}).get("name", "NewsAPI"),
                                               "published_at": a.get("publishedAt", "")}
                                              for a in data.get("articles", [])
                                              if a.get("title") and a["title"] != "[Removed]"]
            except Exception as e:
                logger.warning(f"NewsAPI: {e}")
        else:
            sources["newsapi"] = []

        # Reddit
        if REDDIT_CLIENT_ID:
            try:
                import praw
                r = praw.Reddit(client_id=REDDIT_CLIENT_ID, client_secret=REDDIT_CLIENT_SECRET,
                               user_agent=REDDIT_USER_AGENT, check_for_async=False)
                posts = []
                for sub in REDDIT_SUBREDDITS:
                    try:
                        for p in r.subreddit(sub).hot(limit=5):
                            if not p.stickied:
                                posts.append({"title": p.title, "url": f"https://reddit.com{p.permalink}",
                                              "score": p.score, "num_comments": p.num_comments,
                                              "subreddit": sub, "created_utc": p.created_utc})
                    except Exception:
                        pass
                sources["reddit"] = posts
            except Exception as e:
                logger.warning(f"Reddit: {e}")
                sources["reddit"] = []
        else:
            sources["reddit"] = []

    # Google Trends (sync)
    try:
        sources["google_trends"] = await fetch_google_trends(CONTENT_KEYWORDS)
    except Exception as e:
        logger.error(f"Google Trends: {e}")
        sources["google_trends"] = []

    cache.set_source_counts({n: len(v) for n, v in sources.items()})

    # Aggregate
    trends = aggregator.merge_and_score(sources)

    # Enrich (additive — failure is non-fatal)
    try:
        from core.enrichment import enrich_trends
        trends = enrich_trends(trends)
    except Exception as e:
        logger.warning(f"Enrichment layer skipped: {e}")

    if trends:
        cache.update(trends)
    else:
        # Never wipe a good feed because a refresh came back empty
        # (all sources failed/timed out/rate-limited).
        msg = "Refresh returned 0 trends; kept previous data"
        logger.warning(msg)
        cache.add_error(msg)

    total = sum(len(v) for v in sources.values())
    logger.info(f"Done: {total} raw -> {len(trends)} unique")
    for t in trends[:3]:
        srcs = ",".join(t.get("sources", [t["source"]])[:2])
        logger.info(f"  #{t['rank']} [{t['trend_score']}] [{srcs}] {t['title'][:70]}")
    return trends


async def refresh_loop():
    logger.info(f"Auto-refresh every {REFRESH_INTERVAL_MINUTES}m")
    while True:
        try:
            await run_pipeline()
        except Exception as e:
            logger.error(f"Loop crash: {e}")
            cache.add_error(str(e)[:150])
        await asyncio.sleep(REFRESH_INTERVAL_MINUTES * 60)
