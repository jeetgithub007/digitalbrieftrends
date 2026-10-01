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

from fastapi import FastAPI, Query, Request, HTTPException
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
from core.enrichment import (
    generate_article, generate_social, generate_content_suite,
    normalize_category, compute_velocity, compute_sentiment
)
from core.articles import article_store
from core.article_generator import generate_full_article


# ═══ Trend serialization (includes enrichment fields) ═══
def _serialize_trend(t):
    """Serialize a trend with all enrichment fields (optional/graceful)."""
    return {
        "rank": t.get("rank"),
        "title": t.get("title", ""),
        "title_hi": t.get("title_hi", ""),
        "url": t.get("url", ""),
        "trend_score": t.get("trend_score", 0),
        "seo_score": t.get("seo_score"),
        "growth_percentage": t.get("growth_percentage"),
        "velocity": t.get("velocity") or compute_velocity(t),
        "sentiment": t.get("sentiment") or compute_sentiment(t),
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
    path = os.path.join(ROOT, "home.html")
    if os.path.exists(path):
        return open(path, encoding="utf-8").read()
    return HTMLResponse("<h1>Homepage loading...</h1>", status_code=200)

@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard():
    path = os.path.join(ROOT, "dashboard.html")
    if os.path.exists(path):
        return open(path, encoding="utf-8").read()
    return HTMLResponse("<h1>Dashboard loading...</h1>", status_code=200)

@app.get("/admin", response_class=HTMLResponse)
async def admin():
    path = os.path.join(ROOT, "admin.html")
    if os.path.exists(path):
        return open(path, encoding="utf-8").read()
    return HTMLResponse("<h1>Admin loading...</h1>", status_code=200)

@app.get("/privacy", response_class=HTMLResponse)
async def privacy():
    path = os.path.join(ROOT, "privacy.html")
    if os.path.exists(path):
        return open(path, encoding="utf-8").read()
    return HTMLResponse("<h1>Privacy Policy loading...</h1>", status_code=200)

@app.get("/terms", response_class=HTMLResponse)
async def terms():
    path = os.path.join(ROOT, "terms.html")
    if os.path.exists(path):
        return open(path, encoding="utf-8").read()
    return HTMLResponse("<h1>Terms of Service loading...</h1>", status_code=200)

@app.get("/editorial-standards", response_class=HTMLResponse)
async def editorial_standards():
    path = os.path.join(ROOT, "editorial_standards.html")
    if os.path.exists(path):
        return open(path, encoding="utf-8").read()
    return HTMLResponse("<h1>Editorial Standards loading...</h1>", status_code=200)

@app.get("/contact", response_class=HTMLResponse)
async def contact():
    path = os.path.join(ROOT, "contact.html")
    if os.path.exists(path):
        return open(path, encoding="utf-8").read()
    return HTMLResponse("<h1>Contact Editors loading...</h1>", status_code=200)


def render_article_html(tpl, art):
    import html as html_lib
    import json as json_lib
    import re as re_lib

    faq_items = art.get("faq") or []
    faq_html = ""
    faq_schema = []
    if faq_items:
        faq_html += '<section class="faq-section"><h2 style="font-size:1.5rem; font-weight:800; margin-bottom:20px;">❓ Frequently Asked Questions</h2>'
        for f in faq_items:
            q = html_lib.escape(f.get("question", ""))
            a = html_lib.escape(f.get("answer", ""))
            faq_html += f'<div class="faq-item"><div class="faq-question">Q: {q}</div><div class="faq-answer">A: {a}</div></div>'
            faq_schema.append({
                "@type": "Question",
                "name": f.get("question", ""),
                "acceptedAnswer": {
                    "@type": "Answer",
                    "text": f.get("answer", "")
                }
            })
        faq_html += '</section>'

    faq_json_ld = ""
    if faq_schema:
        faq_json_ld = f'<script type="application/ld+json">{json_lib.dumps({"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": faq_schema})}</script>'

    keywords_str = ", ".join(art.get("secondary_keywords") or [])
    pub_date = (art.get("published_at") or "")[:10]

    img_html = f'<img src="{html_lib.escape(art.get("featured_image", ""))}" alt="{html_lib.escape(art.get("image_alt", ""))}" class="featured-img">' if art.get("featured_image") else ''

    source_html = ""
    if art.get("source"):
        src_name = html_lib.escape(art.get("source"))
        src_url = html_lib.escape(art.get("source_url") or "#")
        source_html = f'''<div class="source-attribution">
            📌 <strong>Source Attribution:</strong> Factual reference derived from reporting by <em>{src_name}</em>.
            {f'<a href="{src_url}" target="_blank" rel="noopener">Read original news source &rarr;</a>' if art.get("source_url") else ''}
        </div>'''

    news_schema = json_lib.dumps({
        "@context": "https://schema.org",
        "@type": "NewsArticle",
        "headline": art.get("title", ""),
        "image": [art.get("featured_image", "")],
        "datePublished": art.get("published_at", ""),
        "dateModified": art.get("updated_at", ""),
        "author": [{
            "@type": "Organization",
            "name": art.get("author", "DigitalBrief Editorial Desk"),
            "url": "https://digitalbrief.in"
        }],
        "publisher": {
            "@type": "Organization",
            "name": "DigitalBrief",
            "logo": {
                "@type": "ImageObject",
                "url": "https://digitalbrief.in/static/favicon.svg"
            }
        },
        "description": art.get("meta_description", ""),
        "articleSection": art.get("category", "Technology")
    })

    res = tpl
    res = res.replace("{{ article.seo_title }}", html_lib.escape(art.get("seo_title", "")))
    res = res.replace("{{ article.meta_description }}", html_lib.escape(art.get("meta_description", "")))
    res = res.replace("{{ article.focus_keyword }}", html_lib.escape(art.get("focus_keyword", "")))
    res = res.replace("{{ article.secondary_keywords|join(', ') }}", html_lib.escape(keywords_str))
    res = res.replace("{{ article.social_title or article.seo_title }}", html_lib.escape(art.get("social_title") or art.get("seo_title", "")))
    res = res.replace("{{ article.social_description or article.meta_description }}", html_lib.escape(art.get("social_description") or art.get("meta_description", "")))
    res = res.replace("{{ article.featured_image }}", html_lib.escape(art.get("featured_image", "")))
    res = res.replace("{{ article.category }}", html_lib.escape(art.get("category", "Technology")))
    res = res.replace("{{ article.title }}", html_lib.escape(art.get("title", "")))
    res = res.replace("{{ article.author }}", html_lib.escape(art.get("author", "DigitalBrief Editorial Desk")))
    res = res.replace("{{ article.published_at[:10] if article.published_at else 'Recent' }}", pub_date or "Recent")
    res = res.replace("{{ article.read_time_minutes }}", str(art.get("read_time_minutes", 3)))
    res = res.replace("{{ article.content | safe }}", art.get("content", ""))

    res = res.replace("<!-- NEWS_SCHEMA_PLACEHOLDER -->", f'<script type="application/ld+json">{news_schema}</script>')
    res = res.replace("<!-- FAQ_SCHEMA_PLACEHOLDER -->", faq_json_ld)
    res = res.replace("<!-- FEATURED_IMAGE_PLACEHOLDER -->", img_html)
    res = res.replace("<!-- FAQ_SECTION_PLACEHOLDER -->", faq_html)
    res = res.replace("<!-- SOURCE_ATTRIBUTION_PLACEHOLDER -->", source_html)
    return res


@app.get("/article/{slug}", response_class=HTMLResponse)
async def article_view(slug: str):
    art = article_store.get_by_slug(slug)
    if not art:
        return HTMLResponse("<div style='text-align:center; padding:60px; font-family:sans-serif;'><h1>404 — Article Not Found</h1><p><a href='/'>Back to Home</a></p></div>", status_code=404)
    path = os.path.join(ROOT, "article_view.html")
    if not os.path.exists(path):
        return HTMLResponse("<h1>Template missing</h1>", status_code=500)
    
    tpl_str = open(path, encoding="utf-8").read()
    rendered = render_article_html(tpl_str, art)
    return HTMLResponse(rendered)

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
        import re as _re
        safe = _re.sub(r"https?://\S+", "<url>", str(e))[:200]
        return {"status": "error", "message": safe}


# ═══════════════════════════════════════
# Trend actions (enrichment + content)
# ═══════════════════════════════════════

def _find_trend(rank):
    data, _, _ = cache.get()
    if not data:
        return None
    rank_str = str(rank).strip()
    for t in data:
        if str(t.get("rank", "")).strip() == rank_str:
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


@app.get("/api/trends/{rank}/generator")
async def api_generator(rank: int):
    """Multi-platform content suite generator (LinkedIn, X, Instagram, Newsletter, SEO)."""
    t = _find_trend(rank)
    if not t:
        return {"status": "not_found"}
    return {"status": "ok", "trend": _serialize_trend(t), "suite": generate_content_suite(t)}


@app.get("/api/trends/export")
async def api_export(
        format: str = Query("json", description="json|csv"),
        category: str = Query(None),
        min_score: int = Query(0, ge=0, le=100)):
    """Export trend intelligence data as JSON or CSV."""
    import io, csv, json as _json
    data, _, _ = cache.get()
    if not data:
        return Response(content="No trend data available", media_type="text/plain", status_code=404)

    items = [t for t in data if t.get("trend_score", 0) >= min_score]
    if category:
        norm = normalize_category(category)
        items = [t for t in items if normalize_category(t.get("category")) == norm]

    clean = [_serialize_trend(t) for t in items]

    if format.lower() == "csv":
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["Rank", "Title", "Category", "Trend Score", "SEO Score", "Growth %", "Velocity", "Sentiment", "Publisher", "Sources", "URL", "Description", "Keywords", "Retrieved At"])
        for item in clean:
            writer.writerow([
                item.get("rank"),
                item.get("title"),
                item.get("category"),
                item.get("trend_score"),
                item.get("seo_score"),
                item.get("growth_percentage") or "",
                item.get("velocity"),
                item.get("sentiment"),
                item.get("publisher"),
                ", ".join(item.get("sources", [])),
                item.get("url"),
                item.get("description"),
                ", ".join(item.get("related_keywords", [])),
                item.get("retrieved_at"),
            ])
        headers = {"Content-Disposition": "attachment; filename=digitalbrief_trends.csv"}
        return Response(content=output.getvalue(), media_type="text/csv", headers=headers)

    headers = {"Content-Disposition": "attachment; filename=digitalbrief_trends.json"}
    return Response(content=_json.dumps(clean, indent=2), media_type="application/json", headers=headers)


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


@app.get("/api/channels/live")
async def api_channels_live():
    """Live-state probe results for the Video News channels (cached, single-flight)."""
    from core.channels import get_channel_states
    import time
    try:
        state = await get_channel_states(NEWS_CHANNELS)
        return {
            "checked_at": time.strftime("%Y-%m-%dT%H:%M:%S+05:30", time.localtime(state["checked_at"])),
            "error": state.get("error"),
            "data": state["channels"],
            "total": len(state["channels"]),
        }
    except Exception as e:  # noqa: BLE001 - never take the section down
        return {"checked_at": None, "error": str(e)[:200], "data": [], "total": 0}


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
# ARTICLE PUBLISHING & CMS API
# ═══════════════════════════════════════

@app.get("/api/articles")
async def get_articles(
    status: str = Query(None),
    category: str = Query(None),
    search: str = Query(None),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0)
):
    items, total = article_store.list_articles(status=status, category=category, search=search, limit=limit, offset=offset)
    return {"data": items, "total": total, "limit": limit, "offset": offset}


@app.get("/api/articles/{id_or_slug}")
async def get_article_single(id_or_slug: str):
    art = article_store.get_by_id(id_or_slug) or article_store.get_by_slug(id_or_slug)
    if not art:
        raise HTTPException(status_code=404, detail="Article not found")
    return {"status": "ok", "article": art}


@app.post("/api/articles")
async def create_article(request: Request):
    payload = await request.json()
    if not payload.get("title"):
        raise HTTPException(status_code=400, detail="Title is required")
    created = article_store.create(payload)
    return {"status": "ok", "article": created}


@app.post("/api/articles/generate-and-publish")
async def generate_and_publish_article(request: Request):
    payload = await request.json()
    rank = payload.get("rank")
    trend = payload.get("trend")
    
    if rank and not trend:
        trend = _find_trend(rank)
    
    if not trend:
        raise HTTPException(status_code=400, detail="Valid trend object or rank required")
    
    news_id = trend.get("url") or trend.get("title")
    existing = article_store.get_by_news_id(news_id)
    if existing:
        return {"status": "existing", "article": existing, "message": "Article already generated for this story!"}

    article_data = generate_full_article(trend)
    article_data["original_news_id"] = news_id
    created = article_store.create(article_data)
    return {"status": "ok", "article": created, "message": "Article synthesized and published successfully!"}


@app.put("/api/articles/{article_id}")
async def update_article(article_id: str, request: Request):
    payload = await request.json()
    updated = article_store.update(article_id, payload)
    if not updated:
        raise HTTPException(status_code=404, detail="Article not found")
    return {"status": "ok", "article": updated}


@app.delete("/api/articles/{article_id}")
async def delete_article(article_id: str):
    success = article_store.delete(article_id)
    if not success:
        raise HTTPException(status_code=404, detail="Article not found")
    return {"status": "ok", "message": "Article deleted"}


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
    uvicorn.run(app, host=HOST, port=PORT, reload=False, log_level="info")

