"""MediaCloud fetcher (best-effort).

Contract (docs-verified 2026-08-14): GET /api/v2/stories_public/list,
auth key= query param, rows (max 1000), response is a bare JSON array of
stories (title, url, publish_date MySQL-style, media_name, language).
api.mediacloud.org does not resolve from the local network (2026-08-14) so
this fetcher is best-effort: any failure degrades to [] and the pipeline
stays healthy. Weight is set low (30) so an unverified source cannot
distort rankings.
"""
import logging
import aiohttp
from fetchers._util import clean_url, iso_utc, safe_title

logger = logging.getLogger("trends.mediacloud")
URL = "https://api.mediacloud.org/api/v2/stories_public/list"
_EN_LANGS = {"en", "eng", "en-us", "en-gb", "en-ca", "en-au"}


async def fetch_mediacloud(session, api_key, limit=30, timeout=25):
    if not api_key:
        logger.warning("MediaCloud: no key")
        return []
    articles = []
    params = {"q": "news", "rows": min(limit, 1000), "key": api_key}
    try:
        async with session.get(URL, params=params, timeout=aiohttp.ClientTimeout(total=timeout)) as r:
            if r.status != 200:
                logger.warning(f"MediaCloud: HTTP {r.status}")
                return []
            data = await r.json(content_type=None)
            if isinstance(data, dict):
                stories = data.get("stories") or data.get("results") or []
            elif isinstance(data, list):
                stories = data
            else:
                stories = []
            for a in stories[:limit * 2]:
                t = safe_title(a)
                if not t or len(t) < 6:
                    continue
                lang = (a.get("language") or "").lower()
                if lang and lang not in _EN_LANGS:
                    continue
                articles.append({
                    "title": t,
                    "url": clean_url(a.get("url", "")),
                    "description": (a.get("description") or "")[:240],
                    "published_at": iso_utc(a.get("publish_date", "")),
                    "source": (a.get("media_name") or a.get("name") or "MediaCloud"),
                    "image": a.get("image_url", "") or "",
                })
                if len(articles) >= limit:
                    break
    except Exception as e:
        logger.error(f"MediaCloud: {e}")
    logger.info(f"MediaCloud: {len(articles)}")
    return articles
