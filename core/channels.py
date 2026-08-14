"""Live-state detection for the Video News channels.

The dashboard embeds YouTube news channels. The classic
`/embed/live_stream?channel=ID` pattern shows "Video unavailable" whenever a
channel is not currently broadcasting or YouTube cannot resolve the live
stream for embedding. This module probes each channel's `/live` page and
extracts the *concrete* live video ID (via ytInitialPlayerResponse markers),
so the dashboard can embed the actual video (reliable) or show an honest
off-air card (never a dead iframe).

States per channel:
  live=True    -> playable live stream detected, video_id set
  live=False   -> probe succeeded, channel not broadcasting right now
  live=None    -> probe failed (network/blocked) — caller falls back gracefully

Probes are cached (TTL) and single-flight to avoid hammering YouTube.
"""
import asyncio
import logging
import re
import time

log = logging.getLogger("channels")

LIVE_URL = "https://www.youtube.com/channel/{cid}/live"
PROBE_TTL_S = 300  # 5 minutes

_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/126.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
    "Cookie": "CONSENT=YES+1; SOCS=CAI",
}

_PLAY_OK_RE = re.compile(r'"playabilityStatus"\s*:\s*\{\s*"status"\s*:\s*"OK"')
_VIDEO_ID_RE = re.compile(r'"videoDetails"\s*:\s*\{\s*"videoId"\s*:\s*"([A-Za-z0-9_-]{11})"')

_lock = asyncio.Lock()
_state = {"checked_at": 0.0, "channels": [], "error": None}


async def _probe_one(session, ch):
    """Probe a single channel. Never raises."""
    name = ch.get("name", "?")
    cid = ch.get("youtube")
    if ch.get("embed") != "youtube" or not cid:
        return {"name": name, "live": False, "video_id": None, "probe": "skipped"}
    try:
        async with session.get(
            LIVE_URL.format(cid=cid), headers=_HEADERS,
            timeout=aiohttp_timeout(),
        ) as resp:
            if resp.status != 200:
                return {"name": name, "live": False, "video_id": None, "probe": "http_%s" % resp.status}
            html = await resp.text(errors="ignore")
        play_ok = bool(_PLAY_OK_RE.search(html))
        m = _VIDEO_ID_RE.search(html)
        vid = m.group(1) if m else None
        if play_ok and vid:
            return {"name": name, "live": True, "video_id": vid, "probe": "ok"}
        return {"name": name, "live": False, "video_id": None, "probe": "no_live"}
    except asyncio.CancelledError:
        raise
    except Exception:
        log.warning("channel probe failed (name=%s)", name)
        return {"name": name, "live": None, "video_id": None, "probe": "unknown"}


def aiohttp_timeout():
    import aiohttp
    return aiohttp.ClientTimeout(total=12)


async def get_channel_states(news_channels, force=False):
    """Return cached (or freshly probed) live states for all channels."""
    global _state
    now = time.time()
    if not force and _state["channels"] and (now - _state["checked_at"]) < PROBE_TTL_S:
        return _state
    async with _lock:
        if not force and _state["channels"] and (time.time() - _state["checked_at"]) < PROBE_TTL_S:
            return _state
        try:
            import aiohttp
            targets = [c for c in news_channels if c.get("active", True)]
            async with aiohttp.ClientSession() as session:
                results = await asyncio.gather(
                    *(_probe_one(session, c) for c in targets),
                    return_exceptions=True,
                )
            states = []
            for r in results:
                if isinstance(r, Exception):
                    states.append({"name": "?", "live": None, "video_id": None, "probe": "unknown"})
                else:
                    states.append(r)
            _state = {"checked_at": time.time(), "channels": states, "error": None}
        except Exception as e:  # noqa: BLE001 - keep serving, degrade to fallback
            log.warning("channel probe batch failed: %s", str(e)[:120])
            _state["error"] = str(e)[:200]
            _state["checked_at"] = time.time()
    return _state
