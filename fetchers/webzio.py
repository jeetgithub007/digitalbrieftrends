"""Webz.io News API (Lite plan) fetcher.

Live-verified 2026-08-14: works with the provided key (10 posts/refresh).
Lite plan ~1,000 req/month -> throttled to <=1 call/hour.
"""
import logging, time, aiohttp
from fetchers._util import clean_url, iso_utc, safe_title

logger = logging.getLogger("trends.webzio")
URL = "https://api.webz.io/newsApiLite"

_last_call = 0.0
THROTTLE_SECONDS = 3600  # 1 call/hour (Lite quota)


async def fetch_webzio(session, api_key, limit=20, timeout=25):
    global _last_call
    if not api_key:
        logger.warning("Webz.io: no key")
        return []
    if time.time() - _last_call < THROTTLE_SECONDS:
        logger.info("Webz.io: throttled (1/hour quota guard)")
        return []
    articles = []
    params = {
        "token": api_key,
        "q": "language:english",
        "ts": str(int(time.time() * 1000) - 24 * 3600 * 1000),  # last 24h, ms
    }
    try:
        async with session.get(URL, params=params, timeout=aiohttp.ClientTimeout(total=timeout)) as r:
            if r.status != 200:
                logger.warning(f"Webz.io: HTTP {r.status}")
                return []
            data = await r.json(content_type=None)
            _last_call = time.time()
            for p in (data.get("posts", []) or [])[:limit * 2]:
                t = safe_title(p)
                if not t or len(t) < 6:
                    continue
                thread = p.get("thread", {}) or {}
                if thread.get("language") and thread["language"] != "english":
                    continue
                articles.append({
                    "title": t,
                    "url": clean_url(p.get("url", "")),
                    "description": (p.get("text") or "")[:240],
                    "published_at": iso_utc(p.get("published", "")),
                    "source": (thread.get("site") or thread.get("site_full") or "Webz.io"),
                    "image": thread.get("main_image", "") or "",
                })
                if len(articles) >= limit:
                    break
    except Exception as e:
        logger.error(f"Webz.io: {e}")
    logger.info(f"Webz.io: {len(articles)}")
    return articles
