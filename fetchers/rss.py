"""RSS fetcher — extracts real article title, description, image and date.

Fetches feeds concurrently using aiohttp & feedparser with browser-like User-Agent.
Isolates every feed with Semaphore concurrency limits and timeout guards.
"""
import asyncio, logging, re, html, aiohttp, feedparser
from datetime import datetime, timezone, timedelta

logger = logging.getLogger("trends.rss")

try:
    from core.config import RSS_PER_FEED, RSS_TIMEOUT
except Exception:
    RSS_PER_FEED, RSS_TIMEOUT = 8, 8

_UA = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/126.0 Safari/537.36 DigitalBrief/1.0",
    "Accept": "application/rss+xml, application/xml, text/xml, application/atom+xml, */*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}

_TAG_RE = re.compile(r"<[^>]+>")


def _clean_text(s):
    """Strip HTML tags and collapse whitespace."""
    if not s:
        return ""
    s = _TAG_RE.sub(" ", s)
    s = html.unescape(s)
    return " ".join(s.split())


def _summary(e):
    """Best-effort real summary from a feed entry."""
    for key in ("summary", "description", "content"):
        val = e.get(key)
        if val:
            if isinstance(val, list):
                val = " ".join(
                    (v.get("value", "") if isinstance(v, dict) else str(v)) for v in val
                )
            txt = _clean_text(str(val))
            if len(txt) >= 40:
                return txt
    return ""


def _image(e):
    """Best-effort image URL from a feed entry (multiple XML structures)."""
    for key in ("media_thumbnail", "media_content"):
        val = e.get(key)
        if isinstance(val, list):
            for m in val:
                if isinstance(m, dict) and m.get("url"):
                    return m["url"]
    for enc in e.get("enclosures", []) or []:
        if isinstance(enc, dict) and "image" in str(enc.get("type", "")):
            if enc.get("href"):
                return enc["href"]
    it = e.get("itunes_image")
    if isinstance(it, dict) and it.get("href"):
        return it["href"]
    for key in ("summary", "description", "content"):
        val = e.get(key)
        if isinstance(val, list):
            val = " ".join(
                (v.get("value", "") if isinstance(v, dict) else str(v)) for v in val
            )
        m = re.search(r'<img[^>]+src=["\']([^"\']+)["\']', str(val or ""))
        if m:
            return html.unescape(m.group(1))
    return ""


async def _fetch_single_feed(session, sem, name, url, cutoff):
    entries = []
    async with sem:
        try:
            async with session.get(url, headers=_UA, timeout=aiohttp.ClientTimeout(total=8), ssl=False) as resp:
                if resp.status == 200:
                    raw = await resp.read()
                    parsed = None
                    for enc in ("utf-8", "latin-1"):
                        try:
                            parsed = feedparser.parse(raw.decode(enc))
                            break
                        except Exception:
                            continue
                    if not parsed:
                        parsed = feedparser.parse(raw.decode("utf-8", "ignore"))

                    for e in parsed.entries[:RSS_PER_FEED]:
                        try:
                            pub = None
                            p_parsed = getattr(e, "published_parsed", None) or getattr(e, "updated_parsed", None)
                            if p_parsed and len(p_parsed) >= 6:
                                try:
                                    pub = datetime(*p_parsed[:6], tzinfo=timezone.utc)
                                except Exception:
                                    pub = None
                            if pub and pub < cutoff:
                                continue
                            entries.append({
                                "title": e.get("title", ""),
                                "url": e.get("link", ""),
                                "source": name,
                                "publisher": name,
                                "description": _summary(e),
                                "image_url": _image(e),
                                "published_at": pub.isoformat() if pub else "",
                            })
                        except Exception as e_err:
                            logger.debug(f"RSS entry parse error in {name}: {e_err}")
        except Exception as err:
            logger.debug(f"RSS/{name}: {str(err)[:60]}")
    return entries


async def fetch_rss(feeds):
    cutoff = datetime.now(timezone.utc) - timedelta(days=3)
    sem = asyncio.Semaphore(20)
    all_entries = []
    
    conn = aiohttp.TCPConnector(limit=30, ssl=False)
    async with aiohttp.ClientSession(connector=conn) as session:
        tasks = [_fetch_single_feed(session, sem, name, url, cutoff) for name, url in feeds]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        for res in results:
            if isinstance(res, list):
                all_entries.extend(res)
                
    logger.info(f"RSS fetch complete: {len(all_entries)} articles from {len(feeds)} feeds")
    return all_entries
