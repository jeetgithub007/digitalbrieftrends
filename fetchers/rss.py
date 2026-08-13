"""RSS fetcher — extracts real article title, description, image and date.

Fetches each feed with a browser-like User-Agent (many Indian publishers block
default feed readers), parses RSS/Atom/RDF via feedparser, and isolates every
feed so one unavailable feed can never break the pipeline.
"""
import asyncio, logging, re, html, urllib.request
from datetime import datetime, timezone, timedelta

logger = logging.getLogger("trends.rss")

try:
    from core.config import RSS_PER_FEED, RSS_TIMEOUT
except Exception:
    RSS_PER_FEED, RSS_TIMEOUT = 8, 20

_UA = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/126.0 Safari/537.36",
    "Accept": "application/rss+xml, application/xml, text/xml, */*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}

def _fetch_parse(url):
    """Fetch feed bytes (browser UA) and parse with feedparser (handles RSS2/Atom/RDF)."""
    import feedparser
    req = urllib.request.Request(url, headers=_UA)
    with urllib.request.urlopen(req, timeout=RSS_TIMEOUT) as r:
        raw = r.read(800000)
    for enc in ("utf-8", "latin-1"):
        try:
            return feedparser.parse(raw.decode(enc))
        except Exception:
            continue
    return feedparser.parse(raw.decode("utf-8", "ignore"))

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
    # media_thumbnail / media_content (RSS media namespace)
    for key in ("media_thumbnail", "media_content"):
        val = e.get(key)
        if isinstance(val, list):
            for m in val:
                if isinstance(m, dict) and m.get("url"):
                    return m["url"]
    # enclosures (e.g. Times of India)
    for enc in e.get("enclosures", []) or []:
        if isinstance(enc, dict) and "image" in str(enc.get("type", "")):
            if enc.get("href"):
                return enc["href"]
    # itunes:image (podcast-style feeds)
    it = e.get("itunes_image")
    if isinstance(it, dict) and it.get("href"):
        return it["href"]
    # first <img> inside description/summary HTML (e.g. India Today)
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


async def fetch_rss(feeds):
    entries = []
    cutoff = datetime.now(timezone.utc) - timedelta(days=3)
    for name, url in feeds:
        try:
            loop = asyncio.get_event_loop()
            parsed = await asyncio.wait_for(
                loop.run_in_executor(None, _fetch_parse, url), timeout=RSS_TIMEOUT + 5)
            for e in parsed.entries[:RSS_PER_FEED]:
                pub = None
                if hasattr(e, "published_parsed") and e.published_parsed:
                    pub = datetime(*e.published_parsed[:6], tzinfo=timezone.utc)
                elif hasattr(e, "updated_parsed") and e.updated_parsed:
                    pub = datetime(*e.updated_parsed[:6], tzinfo=timezone.utc)
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
            logger.info(f"RSS/{name}: {min(RSS_PER_FEED, len(parsed.entries))}")
        except Exception as err:
            logger.warning(f"RSS/{name}: {str(err)[:100]}")
        await asyncio.sleep(1)  # gentle rate limiting between feeds
    return entries
