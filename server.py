"""
Trend Pipeline REST API + Dashboard Server
===========================================
FastAPI server that serves:
  - /                     → Landing page (SEO-optimized)
  - /dashboard            → Live trend dashboard
  - /api/trends           → Full trend data (JSON)
  - /api/trends/status    → Pipeline health
  - /api/trends/top       → Top N trends
  - /api/trends/ideas     → Content ideas
  - /docs                 → Swagger API docs
"""
import asyncio
import logging
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles

from config import HOST, PORT, REFRESH_INTERVAL_MINUTES
from cache import cache
from engine import refresh_loop, run_pipeline
from aggregator import TrendSummary

# ---- Logging ----
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("trend-pipeline.server")

# ---- App lifetime ----
IS_VERCEL = os.getenv("VERCEL", "") == "1" or os.path.exists("/vercel")

# Always create app at top level — Vercel needs this for detection
app = FastAPI(title="Trend Pipeline", version="1.0.0", docs_url="/docs")

if not IS_VERCEL:
    # Local mode: start background refresh loop on startup
    @app.on_event("startup")
    async def startup_refresh():
        logger.info("Server starting — pipeline will fetch in background...")
        asyncio.create_task(refresh_loop())

    @app.on_event("shutdown")
    async def shutdown_refresh():
        logger.info("Server shutting down")
else:
    logger.info("Vercel environment detected — pipeline runs on-demand only")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

# Mount static files (favicon, etc.) — local only; Vercel serves these natively
if not IS_VERCEL:
    STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")
    os.makedirs(STATIC_DIR, exist_ok=True)
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


# ═══════════════════════════════════════════════════
# API Endpoints
# ═══════════════════════════════════════════════════

@app.get("/api/trends/status")
async def status():
    """Pipeline health and refresh info."""
    return cache.status()


@app.get("/api/trends")
async def get_trends(
    limit: int = Query(50, ge=1, le=100),
    min_score: int = Query(0, ge=0, le=100),
    source: str = Query(None, description="Filter by source: google_trends, newsapi, reddit, rss"),
    category: str = Query(None, description="Filter by category: AI, Startups, Crypto, etc."),
):
    """Get all trends with optional filters."""
    data, updated_at, refresh_count = cache.get()
    if data is None:
        # Vercel mode: trigger pipeline on first request
        if IS_VERCEL:
            try:
                import asyncio
                asyncio.create_task(run_pipeline())
            except Exception:
                pass
        return {"data": [], "status": "no_data", "message": "Pipeline hasn't completed first fetch yet"}

    # Apply filters
    filtered = []
    for t in data:
        if t["trend_score"] < min_score:
            continue
        if source and source not in t.get("sources", [t["source"]]):
            continue
        if category:
            cat = TrendSummary._guess_category(t)
            if cat.lower() != category.lower():
                continue
        filtered.append(t)

    # Limit
    filtered = filtered[:limit]

    # Clean up raw_data for API response
    clean = []
    for t in filtered:
        clean.append({
            "rank": t["rank"],
            "title": t["title"],
            "url": t.get("url", ""),
            "trend_score": t["trend_score"],
            "sources": t.get("sources", [t.get("source", "")]),
            "description": t.get("description", "")[:200],
            "published_at": t.get("published_at", ""),
            "subreddit": t.get("subreddit"),
            "extra": {k: v for k, v in t.get("raw_data", {}).items()
                      if k not in ("source",)}
        })

    return {
        "data": clean,
        "total": len(clean),
        "pipeline": {
            "last_refresh": cache.status()["last_updated"],
            "refresh_count": refresh_count,
            "next_refresh_minutes": REFRESH_INTERVAL_MINUTES,
            "age_seconds": cache.status().get("age_seconds"),
        },
    }


@app.get("/api/trends/top")
async def get_top(
    n: int = Query(10, ge=1, le=30),
):
    """Top N trending items — quick view."""
    data, _, _ = cache.get()
    if data is None:
        return {"data": [], "status": "no_data"}

    return {
        "data": TrendSummary.top_rising(data, n),
        "total_available": len(data),
    }


@app.get("/api/trends/ideas")
async def get_content_ideas(
    min_score: int = Query(50, ge=0, le=100),
):
    """High-score trends suitable for content/article ideas."""
    data, _, _ = cache.get()
    if data is None:
        return {"data": [], "status": "no_data"}

    return {"data": TrendSummary.content_ideas(data, min_score)}


@app.get("/api/trends/refresh")
async def force_refresh():
    """Manually trigger a pipeline refresh."""
    try:
        await run_pipeline()
        return {"status": "ok", "message": "Refresh complete"}
    except Exception as e:
        return {"status": "error", "message": str(e)}


# ═══════════════════════════════════════════════════
# Pages
# ═══════════════════════════════════════════════════

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LANDING_PATH = os.path.join(BASE_DIR, "landing.html")
DASHBOARD_PATH = os.path.join(BASE_DIR, "dashboard.html")

@app.get("/", response_class=HTMLResponse)
async def landing():
    """Serve the SEO-optimized landing page."""
    if os.path.exists(LANDING_PATH):
        with open(LANDING_PATH, "r", encoding="utf-8") as f:
            return f.read()
    return "<h1>Landing page not found</h1>"


@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard():
    """Serve the live trend dashboard."""
    if os.path.exists(DASHBOARD_PATH):
        with open(DASHBOARD_PATH, "r", encoding="utf-8") as f:
            return f.read()
    return "<h1>Dashboard not found</h1>"


# ═══════════════════════════════════════════════════
# Vercel ASGI handler
# ═══════════════════════════════════════════════════

# Vercel's @vercel/python build wraps this app automatically.
# The `app` object exposed above is the ASGI entry point.
# No additional handler needed — Vercel routes to server.py.


# ═══════════════════════════════════════════════════
# CLI entry (local development)
# ═══════════════════════════════════════════════════

if __name__ == "__main__":
    import uvicorn
    print(f"\n  Trend Pipeline Server")
    print(f"  http://{HOST}:{PORT}            — Landing Page")
    print(f"  http://{HOST}:{PORT}/dashboard  — Live Dashboard")
    print(f"  http://{HOST}:{PORT}/docs       — API Docs (Swagger)")
    print(f"  Refresh interval: {REFRESH_INTERVAL_MINUTES} minutes\n")
    uvicorn.run(app, host=HOST, port=PORT, log_level="info")
