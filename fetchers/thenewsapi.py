"""The News API (thenewsapi.com) fetcher.

Live-verified 2026-08-14: works with the provided key (3 items/refresh on
the free tier, which caps limit even when a higher value is requested).
"""
import logging
import aiohttp
from fetchers._util import clean_url, iso_utc, safe_title

logger = logging.getLogger("trends.thenewsapi")
URL = "https://api.thenewsapi.com/v1/news/all"


async def fetch_thenewsapi(session, api_key, limit=25, timeout=25):
    if not api_key:
        logger.warning("The News API: no key")
        return []
    articles = []
    params = {
        "api_token": api_key,
        "language": "en",
        "limit": min(limit, 25),
        "sort": "published_on",
    }
    try:
        async with session.get(URL, params=params, timeout=aiohttp.ClientTimeout(total=timeout)) as r:
            if r.status != 200:
                logger.warning(f"The News API: HTTP {r.status}")
                return []
            data = await r.json(content_type=None)
            items = data.get("data", []) if isinstance(data, dict) else []
            if not isinstance(items, list):
                items = []
            for a in items[:limit * 2]:
                t = safe_title(a)
                if not t or len(t) < 6:
                    continue
                cats = a.get("categories")
                articles.append({
                    "title": t,
                    "url": clean_url(a.get("url", "")),
                    "description": (a.get("description") or a.get("snippet") or "")[:240],
                    "published_at": iso_utc(a.get("published_at", "")),
                    "source": (a.get("source") or "The News API"),
                    "image": a.get("image_url", "") or "",
                    "category": (cats[0] if isinstance(cats, list) and cats else ""),
                })
                if len(articles) >= limit:
                    break
    except Exception as e:
        logger.error(f"The News API: {e}")
    logger.info(f"The News API: {len(articles)}")
    return articles
