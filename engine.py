"""
Trend Pipeline Engine — orchestrates all fetchers, aggregation, and caching.
"""
import asyncio
import logging
import os
import sys
import traceback

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from cache import cache
from config import (
    CONTENT_KEYWORDS, GOOGLE_TRENDS_PROXY,
    NEWSAPI_KEY, NEWSAPI_COUNTRY, NEWSAPI_CATEGORIES,
    MEDIASTACK_KEY, MEDIASTACK_COUNTRIES, MEDIASTACK_CATEGORIES, MEDIASTACK_LIMIT,
    GNEWS_KEY, GNEWS_COUNTRY, GNEWS_LIMIT,
    CURRENTS_KEY, CURRENTS_CATEGORIES, CURRENTS_LIMIT,
    REDDIT_CLIENT_ID, REDDIT_CLIENT_SECRET, REDDIT_USER_AGENT, REDDIT_SUBREDDITS,
    RSS_FEEDS, TREND_SCORE_WEIGHTS, MULTI_SOURCE_BONUS, MAX_TRENDS,
    REFRESH_INTERVAL_MINUTES,
)
from fetchers.google_trends import GoogleTrendsFetcher
from fetchers.newsapi import NewsAPIFetcher
from fetchers.mediastack import MediastackFetcher
from fetchers.gnews import GNewsFetcher
from fetchers.currents import CurrentsFetcher
from fetchers.reddit import RedditFetcher
from fetchers.rss import RSSFetcher
from aggregator import TrendAggregator, TrendSummary

logger = logging.getLogger("trend-pipeline.engine")

# ─── Initialize all fetchers ───
google    = GoogleTrendsFetcher(proxy=GOOGLE_TRENDS_PROXY)
newsapi   = NewsAPIFetcher(NEWSAPI_KEY, NEWSAPI_COUNTRY, NEWSAPI_CATEGORIES)
mediastack = MediastackFetcher(MEDIASTACK_KEY, MEDIASTACK_COUNTRIES, MEDIASTACK_CATEGORIES, MEDIASTACK_LIMIT)
gnews     = GNewsFetcher(GNEWS_KEY, GNEWS_COUNTRY, GNEWS_LIMIT)
currents  = CurrentsFetcher(CURRENTS_KEY, CURRENTS_CATEGORIES, CURRENTS_LIMIT)
reddit    = RedditFetcher(REDDIT_CLIENT_ID, REDDIT_CLIENT_SECRET, REDDIT_USER_AGENT, REDDIT_SUBREDDITS)
rss       = RSSFetcher(RSS_FEEDS)
aggregator = TrendAggregator(TREND_SCORE_WEIGHTS, MULTI_SOURCE_BONUS, MAX_TRENDS)


async def run_pipeline():
    """Execute all fetchers in parallel, aggregate, and update cache."""
    logger.info("=" * 50)
    logger.info("Pipeline refresh started — 7 sources")

    sources = {}

    # Create one shared aiohttp session for all HTTP-based fetchers
    import aiohttp
    async with aiohttp.ClientSession() as session:

        # ═══ ASYNC FETCHERS (run concurrently) ═══
        async def safe_fetch(name, coro):
            try:
                return name, await coro
            except Exception as e:
                logger.error(f"{name} failed: {e}")
                cache.add_error(f"{name}: {str(e)[:100]}")
                return name, []

        # Launch all async fetchers in parallel
        tasks = [
            safe_fetch("newsapi", newsapi.fetch(session)),
            safe_fetch("mediastack", mediastack.fetch(session)),
            safe_fetch("gnews", gnews.fetch(session)),
            safe_fetch("currents", currents.fetch(session)),
            safe_fetch("rss", rss.fetch()),
        ]
        results = await asyncio.gather(*tasks)
        for name, data in results:
            sources[name] = data
            logger.info(f"  {name}: {len(data)} items")

        # Reddit (has its own auth — separate session)
        try:
            sources["reddit"] = await reddit.fetch()
            logger.info(f"  reddit: {len(sources['reddit'])} items")
        except Exception as e:
            logger.error(f"reddit failed: {e}")
            cache.add_error(f"reddit: {str(e)[:100]}")
            sources["reddit"] = []

    # ═══ GOOGLE TRENDS (sync — run in executor) ═══
    try:
        loop = asyncio.get_event_loop()
        sources["google_trends"] = await loop.run_in_executor(
            None, lambda: _build_google_trend_items(google, CONTENT_KEYWORDS)
        )
        logger.info(f"  google_trends: {len(sources['google_trends'])} items")
    except Exception as e:
        logger.error(f"google_trends failed: {e}")
        cache.add_error(f"google_trends: {str(e)[:100]}")
        sources["google_trends"] = []

    # ═══ AGGREGATE ═══
    trends = aggregator.merge_and_score(sources)
    cache.update(trends)

    # Summary
    total_raw = sum(len(v) for v in sources.values())
    logger.info(f"Pipeline done: {total_raw} raw → {len(trends)} unique trends")
    for t in trends[:5]:
        src_tags = ",".join(t.get("sources", [t.get("source", "")])[:3])
        logger.info(f"  #{t['rank']:3d} [{t['trend_score']:3d}] [{src_tags}] {t['title'][:70]}")

    return trends


def _build_google_trend_items(google, keywords):
    """Build trend items from Google Trends data (sync)."""
    items = []

    suggestions = google.fetch_suggestions(keywords[:8])
    for kw, sug_list in suggestions.items():
        for title in sug_list:
            items.append({
                "title": title,
                "source": "google_trends",
                "query": kw,
                "search_volume": 0,
            })

    regional = google.fetch_regional(keywords[:4])
    for kw, regions in regional.items():
        for r in regions:
            if r["score"] > 60:
                items.append({
                    "title": f"{kw} trending in {r['region']}",
                    "source": "google_trends",
                    "search_volume": r["score"] * 10,
                })

    return items


async def refresh_loop():
    """Background loop: refresh pipeline every N minutes."""
    logger.info(f"Pipeline refresh loop started (interval: {REFRESH_INTERVAL_MINUTES}m)")
    while True:
        try:
            await run_pipeline()
        except Exception as e:
            logger.error(f"Pipeline loop crashed: {e}\n{traceback.format_exc()}")
            cache.add_error(f"Loop crash: {str(e)[:150]}")
        await asyncio.sleep(REFRESH_INTERVAL_MINUTES * 60)
