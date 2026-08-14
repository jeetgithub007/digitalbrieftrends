"""Real-data live widgets for the dashboard: weather, markets, cricket, sports.

Sources (all key-free, live-verified):
  - Weather:   Open-Meteo (current + 6-day forecast)
  - Markets:   Yahoo Finance chart API (price, change, sparkline) per symbol
  - Cricket:   Cricbuzz live-cricket-scores page (Next.js flight payload)
  - Sports:    ESPN site API (soccer EPL, NFL, tennis, F1 scoreboards)

Every section degrades independently and honestly: a failed source returns
`ok: false` with a short reason — never fabricated data. Results are cached
(single-flight, TTL) to respect free-tier rate limits.
"""
import asyncio
import json
import logging
import os
import re
import time

log = logging.getLogger("widgets")

BUNDLE_TTL_S = 120
_MAX_CACHE_AGE_S = 3600

WEATHER_LAT = float(os.environ.get("WEATHER_LAT", "28.6139"))
WEATHER_LON = float(os.environ.get("WEATHER_LON", "77.2090"))
WEATHER_CITY = os.environ.get("WEATHER_CITY", "New Delhi")

STOCK_SYMBOLS = ["^NSEI", "^BSESN", "RELIANCE.NS", "TCS.NS", "INFY.NS", "GC=F", "INR=X"]
STOCK_NAMES = {
    "^NSEI": "NIFTY 50", "^BSESN": "SENSEX", "RELIANCE.NS": "Reliance",
    "TCS.NS": "TCS", "INFY.NS": "Infosys", "GC=F": "Gold (USD/oz)", "INR=X": "USD/INR",
}

WMO = {
    0: ("Clear sky", "☀️"), 1: ("Mostly clear", "🌤️"), 2: ("Partly cloudy", "⛅"),
    3: ("Overcast", "☁️"), 45: ("Foggy", "🌫️"), 48: ("Foggy", "🌫️"),
    51: ("Light drizzle", "🌦️"), 53: ("Drizzle", "🌦️"), 55: ("Heavy drizzle", "🌧️"),
    61: ("Light rain", "🌦️"), 63: ("Rain", "🌧️"), 65: ("Heavy rain", "🌧️"),
    71: ("Light snow", "🌨️"), 73: ("Snow", "🌨️"), 75: ("Heavy snow", "❄️"),
    80: ("Rain showers", "🌦️"), 81: ("Rain showers", "🌧️"), 82: ("Violent showers", "⛈️"),
    95: ("Thunderstorm", "⛈️"), 96: ("Thunderstorm", "⛈️"), 99: ("Thunderstorm", "⛈️"),
}

_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
}

_lock = asyncio.Lock()
_state = {"checked_at": 0.0, "data": None, "error": None}


# ── weather ────────────────────────────────────────────────────────────────
async def _fetch_weather(session):
    params = {
        "latitude": WEATHER_LAT, "longitude": WEATHER_LON,
        "current": "temperature_2m,relative_humidity_2m,apparent_temperature,is_day,precipitation,weather_code,wind_speed_10m",
        "daily": "weather_code,temperature_2m_max,temperature_2m_min",
        "timezone": "auto", "forecast_days": 6,
    }
    async with session.get("https://api.open-meteo.com/v1/forecast", params=params, timeout=15) as r:
        if r.status != 200:
            return {"ok": False, "error": "weather service unavailable (HTTP %s)" % r.status}
        j = await r.json()
    cur = j.get("current") or {}
    daily = j.get("daily") or {}
    code = int(cur.get("weather_code") or 0)
    label, icon = WMO.get(code, ("Unknown", "🌡️"))
    days = []
    times = daily.get("time") or []
    for i in range(min(len(times), 6)):
        dc = int((daily.get("weather_code") or [0])[i] or 0)
        dl, di = WMO.get(dc, ("Unknown", "🌡️"))
        days.append({
            "date": times[i], "label": dl, "icon": di,
            "max": (daily.get("temperature_2m_max") or [None])[i],
            "min": (daily.get("temperature_2m_min") or [None])[i],
        })
    return {
        "ok": True,
        "city": WEATHER_CITY,
        "temp": cur.get("temperature_2m"),
        "feels": cur.get("apparent_temperature"),
        "humidity": cur.get("relative_humidity_2m"),
        "wind": cur.get("wind_speed_10m"),
        "precipitation": cur.get("precipitation"),
        "is_day": cur.get("is_day"),
        "code": code, "label": label, "icon": icon,
        "days": days,
    }


# ── stocks ─────────────────────────────────────────────────────────────────
async def _fetch_stock(session, symbol):
    url = "https://query1.finance.yahoo.com/v8/finance/chart/" + symbol.replace("^", "%5E")
    async with session.get(url, params={"range": "5d", "interval": "1d"}, timeout=15) as r:
        if r.status != 200:
            return None
        j = await r.json()
    res = (j.get("chart", {}).get("result") or [{}])[0]
    meta = res.get("meta") or {}
    closes = ((res.get("indicators", {}).get("quote") or [{}])[0].get("close")) or []
    closes = [c for c in closes if isinstance(c, (int, float))]
    price = meta.get("regularMarketPrice")
    prev = meta.get("chartPreviousClose") or meta.get("previousClose")
    if price is None or prev in (None, 0):
        return None
    return {
        "symbol": symbol, "name": STOCK_NAMES.get(symbol, symbol),
        "price": round(float(price), 2),
        "change": round(float(price) - float(prev), 2),
        "change_pct": round((float(price) - float(prev)) / float(prev) * 100, 2),
        "spark": [round(float(c), 2) for c in closes[-8:]],
    }


async def _fetch_stocks(session):
    results = await asyncio.gather(*(_fetch_stock(session, s) for s in STOCK_SYMBOLS), return_exceptions=True)
    rows = []
    for res in results:
        if isinstance(res, Exception) or res is None:
            continue
        rows.append(res)
    if not rows:
        return {"ok": False, "error": "market data temporarily unavailable"}
    return {"ok": True, "rows": rows}


# ── cricket (Cricbuzz flight payload) ──────────────────────────────────────
_FLIGHT_RE = re.compile(r'self\.__next_f\.push\(\[1,("(?:[^"\\]|\\.)*")\]\)')
_MATCH_RE = re.compile(r'\{"matchInfo":')


def _parse_flight_matches(text):
    payloads = _FLIGHT_RE.findall(text)
    if not payloads:
        return []
    decoded = "".join(json.loads(p) for p in payloads)
    matches = []
    for m in _MATCH_RE.finditer(decoded):
        start = m.start()
        depth = 0
        for k in range(start, len(decoded)):
            if decoded[k] == "{":
                depth += 1
            elif decoded[k] == "}":
                depth -= 1
                if depth == 0:
                    try:
                        obj = json.loads(decoded[start:k + 1])
                    except Exception:
                        obj = None
                    break
        if not obj:
            continue
        mi = obj.get("matchInfo") or {}
        if not mi.get("matchId"):
            continue
        t1 = (mi.get("team1") or {}).get("teamName") or "TBA"
        t2 = (mi.get("team2") or {}).get("teamName") or "TBA"
        s1 = (mi.get("team1") or {}).get("teamSName") or t1[:3].upper()
        s2 = (mi.get("team2") or {}).get("teamSName") or t2[:3].upper()

        def last_innings(side_key):
            side = (obj.get("matchScore") or {}).get(side_key) or {}
            inngs = side.get("inngs1") or {}
            if isinstance(inngs, dict) and inngs.get("runs") is not None:
                return {"runs": inngs.get("runs"), "wkts": inngs.get("wickets"), "overs": inngs.get("overs")}
            return None

        matches.append({
            "matchId": str(mi.get("matchId")),
            "series": mi.get("seriesName") or "",
            "desc": mi.get("matchDesc") or "",
            "format": mi.get("matchFormat") or "",
            "state": mi.get("state") or "",
            "status": mi.get("status") or "",
            "team1": {"name": t1, "sname": s1, "score": last_innings("team1Score")},
            "team2": {"name": t2, "sname": s2, "score": last_innings("team2Score")},
        })
    # dedupe by matchId
    seen, uniq = set(), []
    for mt in matches:
        if mt["matchId"] not in seen:
            seen.add(mt["matchId"])
            uniq.append(mt)
    return uniq


async def _fetch_cricket(session):
    async with session.get("https://www.cricbuzz.com/live-cricket-scores/", timeout=20) as r:
        if r.status != 200:
            return {"ok": False, "error": "cricket scores unavailable (HTTP %s)" % r.status}
        text = await r.text()
    matches = _parse_flight_matches(text)
    if not matches:
        return {"ok": True, "matches": [], "note": "No matches right now"}
    order = {"In Progress": 0, "Preview": 1, "Completed": 2}
    matches.sort(key=lambda m: order.get(m["state"], 9))
    return {"ok": True, "matches": matches[:8]}


# ── other sports (ESPN) ────────────────────────────────────────────────────
_SPORT_LEAGUES = [
    ("soccer/eng.1", "Premier League", "⚽"),
    ("football/nfl", "NFL", "🏈"),
    ("tennis/atp", "Tennis · ATP", "🎾"),
    ("racing/f1", "Formula 1", "🏎️"),
]


async def _fetch_sport(session, path):
    url = "https://site.web.api.espn.com/apis/site/v2/sports/" + path + "/scoreboard"
    async with session.get(url, timeout=15) as r:
        if r.status != 200:
            return None
        j = await r.json()
    events = []
    for e in (j.get("events") or [])[:5]:
        comp = (e.get("competitions") or [{}])[0]
        status = (comp.get("status") or {}).get("type") or {}
        st_label = status.get("description") or "Scheduled"
        teams = []
        for c in comp.get("competitors") or []:
            tm = c.get("team") or {}
            score = c.get("score")
            teams.append({
                "name": tm.get("displayName") or tm.get("abbreviation") or "?",
                "abbr": tm.get("abbreviation") or "",
                "score": score if score not in (None, "") else None,
            })
        events.append({"name": e.get("name") or "", "status": st_label, "teams": teams})
    return events


async def _fetch_sports(session):
    results = await asyncio.gather(*(_fetch_sport(session, p) for p, _, _ in _SPORT_LEAGUES), return_exceptions=True)
    leagues = []
    for (label, icon), res in zip([(l, i) for _, l, i in _SPORT_LEAGUES], results):
        if isinstance(res, Exception) or res is None:
            continue
        leagues.append({"name": label, "icon": icon, "events": res})
    if not leagues:
        return {"ok": False, "error": "sports data temporarily unavailable"}
    return {"ok": True, "leagues": leagues}


# ── bundle ─────────────────────────────────────────────────────────────────
async def _build():
    import aiohttp
    timeout = aiohttp.ClientTimeout(total=25)
    async with aiohttp.ClientSession(headers=_HEADERS, timeout=timeout) as session:
        weather, stocks, cricket, sports = await asyncio.gather(
            _fetch_weather(session),
            _fetch_stocks(session),
            _fetch_cricket(session),
            _fetch_sports(session),
            return_exceptions=True,
        )
    sections = {}
    for name, res in (("weather", weather), ("stocks", stocks), ("cricket", cricket), ("sports", sports)):
        if isinstance(res, Exception):
            sections[name] = {"ok": False, "error": "source request failed"}
        else:
            sections[name] = res
    return {"sections": sections, "generated_at": time.strftime("%Y-%m-%dT%H:%M:%S+05:30")}


async def get_widgets(force=False):
    """Return cached (or freshly built) widget bundle. Never raises."""
    global _state
    now = time.time()
    if not force and _state["data"] and (now - _state["checked_at"]) < BUNDLE_TTL_S:
        return _state
    async with _lock:
        if not force and _state["data"] and (time.time() - _state["checked_at"]) < BUNDLE_TTL_S:
            return _state
        try:
            data = await _build()
            _state = {"checked_at": time.time(), "data": data, "error": None}
        except asyncio.CancelledError:
            raise
        except Exception as e:  # noqa: BLE001 - keep serving
            log.warning("widget bundle failed: %s", str(e)[:120])
            _state["error"] = str(e)[:200]
            _state["checked_at"] = time.time()
    return _state
