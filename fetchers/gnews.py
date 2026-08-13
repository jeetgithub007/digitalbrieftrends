"""GNews fetcher."""
import asyncio, logging, aiohttp
logger = logging.getLogger("trends.gnews")

async def fetch_gnews(session, api_key, limit=20):
    if not api_key:
        logger.warning("GNews: no key")
        return []
    articles = []
    for cat in ["technology", "business", "science", "general"]:
        try:
            params = {"token": api_key, "country": "in", "category": cat,
                      "max": min(limit, 10), "lang": "en"}
            async with session.get("https://gnews.io/api/v4/top-headlines", params=params) as r:
                if r.status == 200:
                    data = await r.json()
                    for a in data.get("articles", []):
                        t = a.get("title", "").strip()
                        if t and len(t) > 5:
                            src = a.get("source", {})
                            articles.append({"title": t, "url": a.get("url", ""),
                                             "description": (a.get("description") or "")[:200],
                                             "published_at": a.get("publishedAt", ""),
                                             "source": src.get("name", "GNews") if isinstance(src, dict) else "GNews"})
                else:
                    logger.warning(f"GNews/{cat}: HTTP {r.status}")
            await asyncio.sleep(2)
        except Exception as e:
            logger.error(f"GNews/{cat}: {e}")
    logger.info(f"GNews: {len(articles)}")
    return articles
