"""Mediastack fetcher."""
import logging, aiohttp
logger = logging.getLogger("trends.mediastack")

async def fetch_mediastack(session, api_key, limit=20):
    if not api_key:
        logger.warning("Mediastack: no key")
        return []
    try:
        params = {"access_key": api_key, "countries": "in,us",
                  "categories": "technology,business,science",
                  "limit": limit, "sort": "published_desc", "languages": "en"}
        async with session.get("http://api.mediastack.com/v1/news", params=params) as r:
            if r.status == 200:
                data = await r.json()
                articles = []
                for a in data.get("data", []):
                    t = a.get("title", "").strip()
                    if t and len(t) > 5:
                        articles.append({"title": t, "url": a.get("url", ""),
                                         "description": (a.get("description") or "")[:200],
                                         "published_at": a.get("published_at", ""),
                                         "source": a.get("source", "Mediastack")})
                logger.info(f"Mediastack: {len(articles)}")
                return articles
            logger.warning(f"Mediastack: HTTP {r.status}")
    except Exception as e:
        logger.error(f"Mediastack: {e}")
    return []
