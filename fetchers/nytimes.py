"""NYTimes Top Stories API fetcher (home section).

Live-verified 2026-08-14: works with the provided key (~22 items/refresh).
Use api-key ONLY — passing the NYT app-id as a query param triggered HTTP 503.
"""
import logging
import aiohttp
from fetchers._util import clean_url, iso_utc, safe_title

logger = logging.getLogger("trends.nytimes")
URL = "https://api.nytimes.com/svc/topstories/v2/home.json"

# Preferred multimedia formats, best -> acceptable
_IMG_ORDER = ("superJumbo", "Jumbo", "Large", "largeHorizontal375", "mediumThreeByTwo210", "thumbLarge")


def _pick_image(multimedia):
    if not isinstance(multimedia, list) or not multimedia:
        return ""
    for fmt in _IMG_ORDER:
        for m in multimedia:
            if isinstance(m, dict) and m.get("format") == fmt and isinstance(m.get("url"), str):
                return m["url"]
    for m in multimedia:
        if isinstance(m, dict) and isinstance(m.get("url"), str):
            return m["url"]
    return ""


async def fetch_nytimes(session, api_key, limit=40, timeout=25, app_id=""):
    if not api_key:
        logger.warning("NYTimes: no key")
        return []
    articles = []
    params = {"api-key": api_key}
    headers = {"Accept": "application/json"}
    try:
        async with session.get(URL, params=params, headers=headers,
                               timeout=aiohttp.ClientTimeout(total=timeout)) as r:
            if r.status != 200:
                logger.warning(f"NYTimes: HTTP {r.status}")
                return []
            data = await r.json(content_type=None)
            items = data.get("results", []) if isinstance(data, dict) else []
            if not isinstance(items, list):
                items = []
            for a in items[:limit * 2]:
                t = safe_title(a)
                if not t or len(t) < 6:
                    continue
                byline = a.get("byline")
                articles.append({
                    "title": t,
                    "url": clean_url(a.get("url", "")),
                    "description": (a.get("abstract") or "")[:240],
                    "published_at": iso_utc(a.get("published_date", "")),
                    "source": (byline.replace("By ", "") if isinstance(byline, str) else "NYTimes"),
                    "image": _pick_image(a.get("multimedia")),
                    "category": a.get("section", ""),
                })
                if len(articles) >= limit:
                    break
    except Exception as e:
        logger.error(f"NYTimes: {e}")
    logger.info(f"NYTimes: {len(articles)}")
    return articles
