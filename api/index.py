"""
Vercel serverless entry point for Trend Pipeline.
Self-contained FastAPI app — built for Vercel's @vercel/python runtime.
"""
import sys
import os
import asyncio
import logging

# Ensure project root is on Python path (Vercel root = repo root)
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# ---- Logging ----
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(name)s] %(levelname)s: %(message)s")
logger = logging.getLogger("trend-pipeline.vercel")

# ---- Build FastAPI App ----
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse

# ═══ EXPORT: app at module level (required by Vercel) ═══
app = FastAPI(title="Trend Pipeline", version="1.0.0", docs_url="/docs")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

# ═══ Import pipeline components ═══
from config import REFRESH_INTERVAL_MINUTES
from cache import cache
from engine import run_pipeline
from aggregator import TrendSummary

# ═══ Page routes ═══
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LANDING_PATH = os.path.join(BASE_DIR, "landing.html")
DASHBOARD_PATH = os.path.join(BASE_DIR, "dashboard.html")


@app.get("/", response_class=HTMLResponse)
async def landing():
    if os.path.exists(LANDING_PATH):
        with open(LANDING_PATH, "r", encoding="utf-8") as f:
            return f.read()
    return "<h1>Trend Pipeline</h1><p>Landing page not found.</p>"


@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard():
    if os.path.exists(DASHBOARD_PATH):
        with open(DASHBOARD_PATH, "r", encoding="utf-8") as f:
            return f.read()
    return "<h1>Dashboard</h1><p>Dashboard not found.</p>"


# ═══ API Endpoints ═══

@app.get("/api/trends/status")
async def status():
    return cache.status()


@app.get("/api/trends")
async def get_trends(
    limit: int = Query(50, ge=1, le=100),
    min_score: int = Query(0, ge=0, le=100),
    source: str = Query(None),
    category: str = Query(None),
):
    data, updated_at, refresh_count = cache.get()
    if data is None:
        # Trigger pipeline on first request (Vercel serverless — fire-and-forget)
        try:
            asyncio.create_task(run_pipeline())
        except Exception:
            pass
        return {"data": [], "status": "no_data", "message": "Pipeline initializing — retry in 30 seconds"}

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

    filtered = filtered[:limit]
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
            "extra": {k: v for k, v in t.get("raw_data", {}).items() if k not in ("source",)},
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
async def get_top(n: int = Query(10, ge=1, le=30)):
    data, _, _ = cache.get()
    if data is None:
        return {"data": [], "status": "no_data"}
    return {"data": TrendSummary.top_rising(data, n), "total_available": len(data)}


@app.get("/api/trends/ideas")
async def get_content_ideas(min_score: int = Query(50, ge=0, le=100)):
    data, _, _ = cache.get()
    if data is None:
        return {"data": [], "status": "no_data"}
    return {"data": TrendSummary.content_ideas(data, min_score)}


@app.get("/api/trends/refresh")
async def force_refresh():
    try:
        await run_pipeline()
        return {"status": "ok", "message": "Refresh complete"}
    except Exception as e:
        return {"status": "error", "message": str(e)}
