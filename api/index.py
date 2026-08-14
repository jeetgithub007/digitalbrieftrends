"""
DigitalBrief Trend Pipeline — Unified Entry Point
==================================================
Works locally (python api/index.py) AND on Vercel.
All routes, pages, and API endpoints in one file.
"""
import sys, os, asyncio, logging

# Path setup — works in both local and Vercel environments
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(name)s] %(levelname)s: %(message)s", datefmt="%H:%M:%S")
logger = logging.getLogger("trends")

from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, FileResponse, Response
from fastapi.staticfiles import StaticFiles

# ═══ APP (at module level — required by Vercel) ═══
app = FastAPI(title="Trend Pipeline", version="2.0", docs_url="/docs")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

# Static files
_STATIC = os.path.join(ROOT, "static")
if os.path.isdir(_STATIC):
    app.mount("/static", StaticFiles(directory=_STATIC), name="static")

# ═══ Imports (after app to avoid circular issues) ═══
from core.config import IS_VERCEL, REFRESH_INTERVAL_MINUTES, NEWS_CHANNELS
from core.cache import cache
from core.engine import run_pipeline, refresh_loop
from core.aggregator import TrendSummary
from core.enrichment import generate_article, generate_social, normalize_category


# ═══ Trend serialization (includes enrichment fields) ═══
def _serialize_trend(t):
    """Serialize a trend with all enrichment fields (optional/graceful)."""
    return {
        "rank": t.get("rank"),
        "title": t.get("title", ""),
        "url": t.get("url", ""),
        "trend_score": t.get("trend_score", 0),
        "seo_score": t.get("seo_score"),
        "growth_percentage": t.get("growth_percentage"),
        "category": normalize_category(t.get("category")),
        "publisher": (t.get("publisher") or (t.get("raw_data") or {}).get("publisher", "") or ""),
        "sources": t.get("sources", [t.get("source", "")]),
        "description": (t.get("description") or "")[:200],
        "published_at": t.get("published_at", ""),
        "subreddit": t.get("subreddit"),
        "image_url": t.get("image_url", ""),
        "image_source": t.get("image_source", ""),
        "image_license": t.get("image_license", ""),
        "related_keywords": t.get("related_keywords", []),
        "related_topics": t.get("related_topics", []),
        "region": t.get("region", ""),
        "language": t.get("language", "en"),
        "retrieved_at": t.get("retrieved_at", ""),
        "saved": t.get("title", "") in cache.saved_titles(),
        "dismissed": t.get("title", "") in cache.dismissed_titles(),
    }

# ═══════════════════════════════════════
# PAGES
# ═══════════════════════════════════════

@app.get("/", response_class=HTMLResponse)
async def home():
    path = os.path.join(ROOT, "dashboard.html")
    if os.path.exists(path):
        return open(path, encoding="utf-8").read()
    return HTMLResponse("<h1>Dashboard loading...</h1>", status_code=200)

@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard():
    path = os.path.join(ROOT, "dashboard.html")
    if os.path.exists(path):
        return open(path, encoding="utf-8").read()
    return HTMLResponse("<h1>Dashboard loading...</h1>", status_code=200)

@app.get("/robots.txt")
async def robots():
    base = os.getenv("SITE_URL", "https://digitalbrief.in").rstrip("/")
    return Response(
        content=f"User-agent: *\nAllow: /\n\nSitemap: {base}/sitemap.xml\n",
        media_type="text/plain",
    )

@app.get("/sitemap.xml")
async def sitemap():
    base = os.getenv("SITE_URL", "https://digitalbrief.in").rstrip("/")
    urls = [f"{base}/"]
    xml = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        + ''.join(
            f"  <url><loc>{u}</loc><changefreq>hourly</changefreq><priority>0.8</priority></url>\n"
            for u in urls
        )
        + '</urlset>'
    )
    return Response(content=xml, media_type="application/xml")

# ═══════════════════════════════════════
# API
# ═══════════════════════════════════════

@app.get("/api/trends/status")
async def api_status():
    return cache.status()

@app.get("/api/trends")
async def api_trends(limit: int = Query(50, ge=1, le=100), min_score: int = Query(0, ge=0, le=100),
                     source: str = Query(None)):
    data, _, _ = cache.get()
    if data is None:
        if IS_VERCEL:
            asyncio.create_task(run_pipeline())
        return {"data": [], "status": "no_data", "message": "Initializing — retry in 30s"}

    filtered = [t for t in data if t["trend_score"] >= min_score
                and (not source or source in t.get("sources", [t["source"]]))]
    filtered = filtered[:limit]
    clean = [_serialize_trend(t) for t in filtered]
    return {"data": clean, "total": len(clean), "pipeline": {"last_refresh": cache.status()["last_updated"],
            "refresh_count": cache.status()["refresh_count"], "age_seconds": cache.status().get("age_seconds")}}


@app.get("/api/trends/enriched")
async def api_trends_enriched(
        limit: int = Query(50, ge=1, le=100),
        sort: str = Query("score", description="score|seo|growth|latest"),
        category: str = Query(None),
        min_score: int = Query(0, ge=0, le=100)):
    """Enriched trends with flexible sorting and category filter."""
    data, _, _ = cache.get()
    if data is None:
        if IS_VERCEL:
            asyncio.create_task(run_pipeline())
        return {"data": [], "status": "no_data", "message": "Initializing — retry in 30s"}

    items = [t for t in data if t["trend_score"] >= min_score]
    if category:
        norm = normalize_category(category)
        items = [t for t in items if normalize_category(t.get("category")) == norm]

    key_map = {
        "score": lambda t: t.get("trend_score", 0),
        "seo": lambda t: t.get("seo_score", 0) or 0,
        "growth": lambda t: t.get("growth_percentage", -1) if t.get("growth_percentage") is not None else -1,
        "latest": lambda t: t.get("published_at", "") or "",
    }
    key = key_map.get(sort, key_map["score"])
    items.sort(key=key, reverse=True)

    clean = [_serialize_trend(t) for t in items[:limit]]
    return {"data": clean, "total": len(clean),
            "categories": sorted({normalize_category(t.get("category")) for t in data})}

@app.get("/api/trends/top")
async def api_top(n: int = Query(10, ge=1, le=30)):
    data, _, _ = cache.get()
    if data is None:
        return {"data": [], "status": "no_data"}
    return {"data": TrendSummary.top_rising(data, n), "total_available": len(data)}

@app.get("/api/trends/ideas")
async def api_ideas(min_score: int = Query(50, ge=0, le=100)):
    data, _, _ = cache.get()
    if data is None:
        return {"data": [], "status": "no_data"}
    return {"data": TrendSummary.content_ideas(data, min_score)}

@app.get("/api/trends/refresh")
async def api_refresh():
    try:
        await run_pipeline()
        return {"status": "ok"}
    except Exception as e:
        return {"status": "error", "message": str(e)}


# ═══════════════════════════════════════
# Trend actions (enrichment + content)
# ═══════════════════════════════════════

def _find_trend(rank):
    data, _, _ = cache.get()
    if not data:
        return None
    for t in data:
        if t.get("rank") == rank:
            return t
    return None


@app.get("/api/trends/{rank}/article")
async def api_article(rank: int):
    t = _find_trend(rank)
    if not t:
        return {"status": "not_found"}
    return {"status": "ok", "trend": _serialize_trend(t), "article": generate_article(t)}


@app.get("/api/trends/{rank}/social")
async def api_social(rank: int):
    t = _find_trend(rank)
    if not t:
        return {"status": "not_found"}
    return {"status": "ok", "trend": _serialize_trend(t), "social": generate_social(t)}


@app.post("/api/trends/{rank}/save")
async def api_save(rank: int):
    t = _find_trend(rank)
    if not t:
        return {"status": "not_found"}
    return cache.save(t["title"])


@app.post("/api/trends/{rank}/dismiss")
async def api_dismiss(rank: int):
    t = _find_trend(rank)
    if not t:
        return {"status": "not_found"}
    return cache.dismiss(t["title"])


@app.get("/api/channels")
async def api_channels():
    """News-channel registry from the source config (URLs sanitized to http/https)."""
    from urllib.parse import urlparse
    import re
    out = []
    for c in NEWS_CHANNELS:
        if not c.get("active", True):
            continue
        entry = dict(c)
        # Sanitize external URLs: only http/https allowed
        u = entry.get("website")
        if u and urlparse(u).scheme not in ("http", "https"):
            entry["website"] = ""
        # YouTube channel ids must look like channel ids (UC + 22 chars)
        y = entry.get("youtube")
        if y and not re.fullmatch(r"UC[\w-]{22}", y):
            entry["youtube"] = ""
        out.append(entry)
    return {"data": out, "total": len(out)}


@app.get("/api/trends/saved")
async def api_saved_list():
    titles = cache.saved_titles()
    data, _, _ = cache.get() or (None, None, 0)
    if data:
        items = [_serialize_trend(t) for t in data if t.get("title") in titles]
    else:
        items = []
    return {"data": items, "total": len(items)}


# ═══════════════════════════════════════
# STARTUP — background refresh (local only)
# ═══════════════════════════════════════

async def _delayed_startup():
    """Delay pipeline start so server can serve requests immediately."""
    await asyncio.sleep(5)
    logger.info("Local mode — background pipeline starting")
    asyncio.create_task(refresh_loop())


@app.on_event("startup")
async def on_startup():
    if not IS_VERCEL:
        asyncio.create_task(_delayed_startup())
        logger.info("Server ready — pipeline will start in 5s")
    else:
        logger.info("Vercel mode — on-demand only")


# ═══════════════════════════════════════
# CLI — run locally
# ═══════════════════════════════════════
if __name__ == "__main__":
    import uvicorn
    from core.config import HOST, PORT
    print(f"\n  Trend Pipeline v2.0")
    print(f"  http://{HOST}:{PORT}            Home (Dashboard)")
    print(f"  http://{HOST}:{PORT}/dashboard  Dashboard")
    print(f"  http://{HOST}:{PORT}/docs       API Docs\n")
    uvicorn.run("api.index:app", host=HOST, port=PORT, reload=False, log_level="info")

