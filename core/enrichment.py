"""
Trend Enrichment — additive, non-breaking intelligence layer.

This module enriches aggregated trends with category, description,
growth, related keywords/topics, SEO score, and a featured image.
It is PURELY ADDITIVE: it reads trend dicts and returns them with
extra optional keys. If enrichment fails, the original trend still
works exactly as before (all fields are optional).
"""
import time
import logging
from datetime import datetime, timezone
from urllib.parse import quote

logger = logging.getLogger("trends.enrichment")

# ─────────────────────────────────────────────────────────────
# Category engine
# ─────────────────────────────────────────────────────────────
CATEGORY_RULES = [
    ("AI", [" ai ", "artificial intelligence", "chatgpt", "gpt", "openai", "llm",
            "machine learning", "deep learning", "neural network", "generative ai",
            "agentic", "anthropic", "claude", "gemini", "deepseek", "mistral",
            "copilot", "codex", "langchain", "prompt engineering", "data science",
            "computer vision", "nlp", "ai agents", "ai-powered", "ai tools"]),
    ("Startups & Funding", ["startup", "funding", "venture", "series a", "series b",
            "series c", "ipo", "raises", "raised", "valuation", "unicorn", "seed",
            "accelerator", "incubator", "fundraise"]),
    ("Crypto & Web3", ["crypto", "bitcoin", "ethereum", "blockchain", "web3", "defi",
            "nft", "token", "stablecoin", "altcoin", "dao", "smart contract"]),
    ("Cybersecurity", ["security", "cyber", "breach", "hack", "malware", "ransomware",
            "phishing", "vulnerability", "zero-day", "ddos", "firewall", "encryption",
            "privacy", "password"]),
    ("Gadgets & Hardware", ["phone", "laptop", "smartphone", "pixel", "iphone",
            "samsung", "galaxy", "watch", "chip", "processor", "gpu", "hardware",
            "device", "tablet", "wearable", "fold", "workstation"]),
    ("Software & Dev", ["software", "developer", "code", "coding", "programming",
            "web dev", "javascript", "python", "api ", "open source", "github",
            "devops", "cloud", "saas", "framework", "app "]),
    ("Marketing & SEO", ["marketing", "seo", "social media", "advertising", "content",
            "wordpress", "ecommerce", "e-commerce", "sales", "brand", "ppc", "email",
            "influencer", "creator"]),
    ("Business & Finance", ["business", "finance", "fintech", "bank", "market",
            "stock", "economy", "revenue", "profit", "merger", "acquisition",
            "investment", "money", "deal"]),
    ("Energy & Climate", ["energy", "climate", "solar", "battery", "ev ", "electric",
            "renewable", "carbon", "sustainability", "grid", "water heater"]),
    ("Science & Health", ["science", "health", "medical", "research", "protein",
            "gene", "biology", "space", "physics", "quantum", "biotech"]),
    ("Auto & Mobility", ["car", "auto", "vehicle", "ev", "tesla", "jaguar", "mobility",
            "self-driving", "autonomous vehicle", "charging"]),
    ("India News", [" india ", "indian", "delhi", "mumbai", "bengaluru", "bangalore",
            "chennai", "kolkata", "hyderabad", "pune", "noida", "gurugram", "kashmir",
            "punjab", "gujarat", "maharashtra", "tamil nadu", "kerala", "uttar pradesh",
            "bihar", "assam", "rajasthan", "west bengal", "jammu", "isro", "chandrayaan",
            "lok sabha", "rajya sabha", "narendra modi", "bjp", "rupee", "sensex", "nifty",
            "gst", "bollywood", "ipl", "adani", "tata group", "mahindra", "sebi",
            "rbi", "chief minister", "ganga", "ndrf", "india vs"]),
]

CATEGORY_STYLE = {
    "AI": ("#6366f1", "🤖"),
    "Startups & Funding": ("#10b981", "🚀"),
    "Crypto & Web3": ("#f59e0b", "₿"),
    "Cybersecurity": ("#ef4444", "🔐"),
    "Gadgets & Hardware": ("#8b5cf6", "📱"),
    "Software & Dev": ("#06b6d4", "💻"),
    "Marketing & SEO": ("#ec4899", "📈"),
    "Business & Finance": ("#14b8a6", "💼"),
    "Energy & Climate": ("#22c55e", "⚡"),
    "Science & Health": ("#0ea5e9", "🔬"),
    "Auto & Mobility": ("#f97316", "🚗"),
    "Technology": ("#64748b", "💡"),
}

RELATED_TOPICS = {
    "AI": ["artificial intelligence", "machine learning", "large language models",
           "AI automation", "generative AI tools", "AI startups"],
    "Startups & Funding": ["startup ecosystem", "venture capital", "funding rounds",
           "unicorn startups", "accelerators", "angel investors"],
    "Crypto & Web3": ["cryptocurrency", "blockchain technology", "decentralized finance",
           "digital assets", "NFT market", "Web3 adoption"],
    "Cybersecurity": ["data breach", "ransomware protection", "network security",
           "zero trust", "threat intelligence", "compliance"],
    "Gadgets & Hardware": ["smartphones", "consumer electronics", "wearables",
           "chip technology", "hardware reviews", "device launches"],
    "Software & Dev": ["developer tools", "open source", "cloud computing",
           "software engineering", "APIs", "DevOps"],
    "Marketing & SEO": ["digital marketing", "search engine optimization", "content strategy",
           "social media marketing", "PPC advertising", "brand growth"],
    "Business & Finance": ["financial markets", "fintech", "business growth",
           "investment", "economy", "corporate strategy"],
    "Energy & Climate": ["renewable energy", "electric vehicles", "clean tech",
           "sustainability", "battery technology", "carbon reduction"],
    "Science & Health": ["scientific research", "biotechnology", "health tech",
           "space exploration", "medical innovation", "climate science"],
    "Auto & Mobility": ["electric vehicles", "autonomous driving", "automotive tech",
           "mobility", "EV charging", "transportation"],
    "Technology": ["tech news", "innovation", "digital transformation",
           "emerging technology", "industry trends", "product launches"],
}

# ─────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────

DEFAULT_CATEGORY = "Technology"

# Case/whitespace-insensitive aliases -> canonical category names.
# Keeps filtering reliable regardless of how a source spells a category.
CATEGORY_ALIASES = {
    "ai": "AI",
    "artificial intelligence": "AI",
    "machine learning": "AI",
    "generative ai": "AI",
    "startups": "Startups & Funding",
    "startup": "Startups & Funding",
    "funding": "Startups & Funding",
    "venture": "Startups & Funding",
    "crypto": "Crypto & Web3",
    "web3": "Crypto & Web3",
    "blockchain": "Crypto & Web3",
    "cyber security": "Cybersecurity",
    "cybersecurity": "Cybersecurity",
    "security": "Cybersecurity",
    "gadgets": "Gadgets & Hardware",
    "hardware": "Gadgets & Hardware",
    "devices": "Gadgets & Hardware",
    "software": "Software & Dev",
    "development": "Software & Dev",
    "developers": "Software & Dev",
    "marketing": "Marketing & SEO",
    "seo": "Marketing & SEO",
    "business": "Business & Finance",
    "finance": "Business & Finance",
    "fintech": "Business & Finance",
    "energy": "Energy & Climate",
    "climate": "Energy & Climate",
    "science": "Science & Health",
    "health": "Science & Health",
    "medical": "Science & Health",
    "auto": "Auto & Mobility",
    "mobility": "Auto & Mobility",
    "technology": "Technology",
    "tech": "Technology",
    "general": "Technology",
    "misc": "Technology",
    "other": "Technology",
    "world": "Technology",
    "news": "Technology",
    "ai": "AI",
    "auto & mobility": "Auto & Mobility",
    "business & finance": "Business & Finance",
    "crypto & web3": "Crypto & Web3",
    "cybersecurity": "Cybersecurity",
    "energy & climate": "Energy & Climate",
    "gadgets & hardware": "Gadgets & Hardware",
    "india news": "India News",
    "marketing & seo": "Marketing & SEO",
    "science & health": "Science & Health",
    "software & dev": "Software & Dev",
    "startups & funding": "Startups & Funding",
    "technology": "Technology",
    "": "Technology",
}


def normalize_category(cat):
    """Return a canonical category name for any input value.

    Handles missing values, whitespace, capitalization and common
    naming variants so filtering always compares like-for-like.
    """
    if not cat:
        return DEFAULT_CATEGORY
    key = " ".join(str(cat).split()).lower()
    return CATEGORY_ALIASES.get(key, " ".join(str(cat).split()))


def categorize(title, description=""):
    """Categorize a trend by title (weighted) + description keywords."""
    t_text = f" {title.lower()} "
    d_text = f" {description.lower()} "
    best = "Technology"
    best_score = 0
    for cat, keywords in CATEGORY_RULES:
        title_hits = sum(1 for kw in keywords if kw in t_text)
        desc_hits = sum(1 for kw in keywords if kw in d_text)
        score = title_hits * 3 + desc_hits  # title keywords weighted 3x
        if score > best_score:
            best, best_score = cat, score
    return normalize_category(best)


def _words(text, limit=80):
    """Truncate text to a word limit."""
    words = text.split()
    return " ".join(words[:limit]) if len(words) > limit else text


def generate_description(trend, category):
    """Return a concise factual description (30–80 words target).

    Prefers the REAL source description (RSS/API summary). For search
    topics without a source article (Google Trends), returns a factual,
    clearly-labelled note — never fabricated news copy.
    """
    existing = (trend.get("description") or "").strip()
    title = trend.get("title", "")
    rank = trend.get("rank", 0)
    if len(existing) >= 30:
        return _words(existing, 80)
    # Factual, data-grounded note for a search topic (not fabricated news)
    region = trend.get("region") or "India / Global"
    return (
        f"Trending search topic in {region} (category: {category}). "
        f"Ranked #{rank} by current rising search interest on Google Trends."
    )


def extract_related_keywords(title, category):
    """Extract related keywords from the title + category."""
    title_words = [w for w in title.lower().split()
                   if w.isalnum() and len(w) > 3 and w not in
                   ("this", "that", "with", "from", "your", "have", "will", "what", "when",
                    "about", "into", "over", "than", "their", "there", "which", "these")]
    keywords = []
    # Significant words from title
    for w in title_words:
        kw = w.rstrip("s,.:;!?") if len(w) > 5 else w
        if kw not in keywords and len(kw) > 3:
            keywords.append(kw)
    # Category seeds
    seeds = RELATED_TOPICS.get(category, [])[:2]
    for s in seeds:
        parts = [p for p in s.split() if len(p) > 3]
        for p in parts:
            if p not in keywords:
                keywords.append(p)
    return keywords[:8]


def related_topics(category, title=""):
    """Return related topics for a category (dedup against title)."""
    pool = RELATED_TOPICS.get(category, RELATED_TOPICS["Technology"])
    return [t for t in pool if t.lower() not in title.lower()][:5]


def compute_growth(trend):
    """Return a realistic growth percentage, or None if unavailable."""
    # Use a real growth signal if a source provided one
    raw = trend.get("raw_data", {}) or {}
    for k in ("growth_percentage", "change_pct", "growth"):
        if raw.get(k) is not None:
            try:
                return int(raw[k])
            except (TypeError, ValueError):
                pass
    # Heuristic from trend score (realistic 10–200% band)
    score = trend.get("trend_score", 0)
    if score >= 90:
        return 120 + (score - 90) * 8
    if score >= 70:
        return 40 + (score - 70) * 4
    if score >= 50:
        return 10 + int((score - 50) * 1.5)
    return None


def compute_seo_score(trend, category):
    """Configurable content/SEO potential score (0–100)."""
    score = 0
    # Popularity (40 pts)
    score += min(40, trend.get("trend_score", 0) * 0.4)
    # Has real source URL (15 pts) — penalise only the old Google Trends explore page
    url = trend.get("url", "")
    if url and "trends.google.com/trends/explore" not in url:
        score += 15
    # Has description (15 pts)
    if (trend.get("description") or "").strip():
        score += 15
    # Title quality (15 pts) — longer, specific titles rank better
    title_len = len(trend.get("title", ""))
    if 20 <= title_len <= 90:
        score += 15
    elif title_len > 10:
        score += 8
    # Multi-source signal (15 pts)
    if len(trend.get("sources", [])) > 1:
        score += 15
    elif trend.get("sources"):
        score += 7
    return min(100, int(score))


def featured_image(trend, category):
    """Return a featured image — real source image if available, else themed SVG."""
    # Prefer a real image from the source feed (RSS media/enclosure)
    raw = trend.get("raw_data") or {}
    real = raw.get("image_url") or raw.get("image") or trend.get("image_url")
    if real and str(real).startswith(("http://", "https://")):
        return {
            "image_url": str(real),
            "image_source": trend.get("source", "source feed"),
            "image_license": "Source feed",
        }
    color, emoji = CATEGORY_STYLE.get(category, CATEGORY_STYLE["Technology"])
    label = category[:20]
    # Inline SVG data URI — always works, no network dependency
    svg = (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="630" viewBox="0 0 1200 630">'
        f'<defs><linearGradient id="g" x1="0" y1="0" x2="1" y2="1">'
        f'<stop offset="0%" stop-color="{color}"/><stop offset="100%" stop-color="#0b0e14"/>'
        f'</linearGradient></defs>'
        f'<rect width="1200" height="630" fill="url(#g)"/>'
        f'<circle cx="1100" cy="80" r="260" fill="#ffffff" opacity="0.06"/>'
        f'<circle cx="120" cy="560" r="220" fill="#ffffff" opacity="0.05"/>'
        f'<text x="80" y="180" font-family="Segoe UI, Arial, sans-serif" font-size="150">{emoji}</text>'
        f'<text x="80" y="360" font-family="Segoe UI, Arial, sans-serif" font-size="64" '
        f'font-weight="700" fill="#ffffff">{_svg_escape(label)}</text>'
        f'<text x="80" y="430" font-family="Segoe UI, Arial, sans-serif" font-size="30" '
        f'fill="#cbd5e1">Trend Intelligence — {category}</text>'
        f'</svg>'
    )
    return {
        "image_url": "data:image/svg+xml;charset=utf-8," + quote(svg),
        "image_source": "DigitalBrief Trend Intelligence",
        "image_license": "Auto-generated (category-themed)",
    }


def _svg_escape(text):
    return (text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))


# ─────────────────────────────────────────────────────────────
# Main enrich
# ─────────────────────────────────────────────────────────────

def enrich_trend(trend):
    """Add enrichment fields to a trend dict (non-destructive)."""
    try:
        title = trend.get("title", "")
        category = categorize(title, trend.get("description", ""))
        img = featured_image(trend, category)
        trend["category"] = normalize_category(category)
        trend["growth_percentage"] = compute_growth(trend)
        trend["description"] = generate_description(trend, category)
        trend["image_url"] = img["image_url"]
        trend["image_source"] = img["image_source"]
        trend["image_license"] = img["image_license"]
        trend["related_keywords"] = extract_related_keywords(title, category)
        trend["related_topics"] = related_topics(category, title)
        trend["region"] = trend.get("region") or "India / Global"
        trend["language"] = trend.get("language") or "en"
        trend["seo_score"] = compute_seo_score(trend, category)
        trend["retrieved_at"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    except Exception as e:
        logger.warning(f"Enrichment failed for '{title[:40]}': {e}")
    return trend


def enrich_trends(trends):
    """Batch enrich — each trend enriched independently; failures ignored."""
    for t in trends:
        enrich_trend(t)
    logger.info(f"Enriched {len(trends)} trends")
    return trends


# ─────────────────────────────────────────────────────────────
# Content generation (article outline + social post)
# ─────────────────────────────────────────────────────────────

def generate_article(trend):
    """Produce an SEO article brief from an enriched trend."""
    title = trend.get("title", "")
    category = trend.get("category", "Technology")
    kws = trend.get("related_keywords", [])
    topics = trend.get("related_topics", [])
    seo = trend.get("seo_score", 0)
    src = trend.get("url", "")
    return {
        "title": title,
        "category": category,
        "seo_score": seo,
        "meta_title": f"{title} — {category} Trend Analysis & Insights",
        "meta_description": f"{trend.get('description', '')[:150]}",
        "target_keywords": kws,
        "outline": [
            f"Introduction: why {title} is trending now",
            f"What {title} means for the {category} space",
            f"Key facts and figures behind the trend",
            "Expert perspectives and industry reactions",
            "How to act on this trend (practical takeaways)",
            "Conclusion and future outlook",
        ],
        "faq": [
            {"q": f"Why is {title} trending?", "a": f"{title} is gaining traction in the {category} space based on rising search interest and cross-source coverage."},
            {"q": f"Who should care about {title}?", "a": f"Content creators, marketers, and professionals in {category} should monitor this trend."},
        ],
        "related_topics": topics,
        "source_url": src,
    }


def generate_social(trend):
    """Produce platform-ready social post variants from an enriched trend."""
    title = trend.get("title", "")
    category = trend.get("category", "Technology")
    growth = trend.get("growth_percentage")
    hook = f"📈 Trending in {category}: {title}"
    if growth is not None:
        hook += f" (+{growth}% growth)"
    body = (f"{hook}\n\n"
            f"{trend.get('description', '')}\n\n"
            f"🔑 Keywords: {', '.join(trend.get('related_keywords', [])[:5])}\n"
            f"🔗 Source: {trend.get('url', '')}")
    hashtags = [f"#{w.replace(' ', '').replace('&', '').replace('-', '')}"
                for w in ([category] + trend.get('related_keywords', [])[:4])]
    return {
        "title": title,
        "hook": hook,
        "post": body,
        "hashtags": hashtags,
        "cta": f"Read the full breakdown on {title} →",
        "image_url": trend.get("image_url", ""),
    }
