"""APITube News API fetcher.

Live-verified 2026-08-14:
- Host: api.apitube.io (www.apitube.io is the marketing site)
- Endpoint: GET /v1/news/everything
- Auth: api_key query param (or X-API-Key header)
- Response: {"status":"ok", "results":[{id, href, title, description, published_at,
  language, author, image, source:{domain,...}, categories, is_breaking, ...}]}
- language=en is a preference, not a hard filter -> client-side English filter.
"""
import logging
from datetime import datetime, timedelta, timezone
import aiohttp
from fetchers._util import clean_url, iso_utc, safe_title

logger = logging.getLogger("trends.apitube")
URL = "https://api.apitube.io/v1/news/everything"


def _image(a):
    img = a.get("image") or ""
    if isinstance(img, dict):
        img = img.get("url") or ""
    return img


async def fetch_apitube(session, api_key, limit=25, timeout=25):
    if not api_key:
        logger.warning("APITube: no key")
        return []
    articles = []
    since = (datetime.now(timezone.utc) - timedelta(hours=48)).strftime("%Y-%m-%dT%H:%M:%S")
    params = {
        "api_key": api_key,
        "language.code": "en",
        "per_page": min(limit, 10),  # Free plan caps at 10
        "sort.by": "published_at",
        "sort.order": "desc",
        "published_at.start": since,
    }
    try:
        async with session.get(URL, params=params, timeout=aiohttp.ClientTimeout(total=timeout)) as r:
            if r.status != 200:
                logger.warning(f"APITube: HTTP {r.status}")
                return []
            data = await r.json(content_type=None)
            items = data.get("results") if isinstance(data, dict) else []
            if not isinstance(items, list):
                items = []
            for a in items[:limit * 3]:
                t = safe_title(a)
                if not t or len(t) < 6:
                    continue
                lang = (a.get("language") or "").lower()
                if lang and not lang.startswith("en"):
                    continue
                src = a.get("source") or {}
                src_name = src.get("domain") if isinstance(src, dict) else src
                articles.append({
                    "title": t,
                    "url": clean_url(a.get("href") or a.get("url") or ""),
                    "description": (a.get("description") or a.get("summary") or "")[:240],
                    "published_at": iso_utc(a.get("published_at", "")),
                    "source": (src_name or a.get("author") or "APITube"),
                    "image": _image(a),
                })
                if len(articles) >= limit:
                    break
    except Exception as e:
        logger.error(f"APITube: {e}")
    logger.info(f"APITube: {len(articles)}")
    return articles
