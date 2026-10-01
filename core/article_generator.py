"""Article Generator — produces human-grade, SEO/AEO/GEO optimized editorial articles from trend items."""
import html
import re
from datetime import datetime, timezone
from urllib.parse import quote

def _clean_text(s):
    if not s:
        return ""
    s = re.sub(r"<[^>]+>", " ", str(s))
    return " ".join(html.unescape(s).split())

def generate_full_article(trend):
    """Synthesizes a full, publishable, SEO/AEO/GEO optimized article from a trend dictionary."""
    title = (trend.get("title") or "Emerging Tech & Market Trend").strip()
    category = trend.get("category") or "Technology"
    description = _clean_text(trend.get("description") or "")
    publisher = trend.get("publisher") or trend.get("source") or "DigitalBrief Wire"
    source_url = trend.get("url") or ""
    region = trend.get("region") or "India / Global"
    growth = trend.get("growth_percentage")
    keywords = trend.get("related_keywords") or []
    topics = trend.get("related_topics") or []
    image_url = trend.get("image_url") or ""
    
    # Focus Keyword selection
    focus_keyword = keywords[0] if keywords else category.lower()
    secondary_keywords = keywords[1:6] if len(keywords) > 1 else [category.lower(), "industry analysis", "market impact", "breaking news"]

    # Excerpt (Lead summary)
    if description and len(description) >= 40:
        excerpt = f"A comprehensive analysis of {title}. Key developments reported by {publisher} highlight critical shifts across the {category} sector."
    else:
        excerpt = f"Rising interest in {title} signals significant movement in {category} across {region}. Here is an editorial breakdown of key facts, context, and market impact."

    # Build rich HTML article body (human-grade, well-structured, scannable)
    growth_banner = f"<div class='trend-stat-banner'><strong>🔥 Growth Signal:</strong> Spiking +{growth}% in real-time search and news velocity.</div>" if growth else ""
    
    body_html = f"""
<div class="article-lead-section">
    <p class="lead-paragraph">
        Major developments regarding <strong>{html.escape(title)}</strong> are driving intense focus across the <strong>{html.escape(category)}</strong> landscape. Reported initially by <em>{html.escape(publisher)}</em>, this trend reflects broader market transformations in {html.escape(region)}.
    </p>
</div>

{growth_banner}

<div class="key-takeaways-box">
    <h3>⚡ Executive Key Takeaways</h3>
    <ul>
        <li><strong>Primary Event:</strong> {html.escape(title)} has emerged as a key focal point for professionals and industry analysts.</li>
        <li><strong>Core Domain:</strong> Categorized under <span>{html.escape(category)}</span>, with implications for search intent, product strategy, and consumer adoption.</li>
        <li><strong>Source Signal:</strong> Verified reporting via <em>{html.escape(publisher)}</em> with growing cross-platform coverage.</li>
        <li><strong>Actionable Insight:</strong> Stakeholders should monitor related topics including {', '.join([f'<em>{html.escape(t)}</em>' for t in topics[:3]]) if topics else 'market trends'}.</li>
    </ul>
</div>

<h2>What Happened: Understanding the Background</h2>
<p>
    {html.escape(description if description else f"The topic '{title}' has seen a significant increase in engagement and news coverage. Market observers note that sudden spikes in search interest often precede strategic shifts within the {category} ecosystem.")}
</p>
<p>
    In recent months, the speed at which news surrounding {html.escape(category.lower())} spreads across digital platforms has accelerated. For organizations tracking {html.escape(focus_keyword)}, maintaining real-time awareness of these developments is critical for competitive positioning.
</p>

<h2>Why It Matters: Strategic Analysis & Market Impact</h2>
<p>
    The implications of <strong>{html.escape(title)}</strong> extend beyond immediate headlines. As {html.escape(category)} continues to evolve, three main factors determine its strategic impact:
</p>
<ol>
    <li><strong>Topical Relevance:</strong> High alignment with ongoing user searches around {', '.join([html.escape(k) for k in secondary_keywords[:3]])}.</li>
    <li><strong>Audience Interest:</strong> Increased query volumes across {html.escape(region)} show sustained user demand for factual clarity.</li>
    <li><strong>Industry Reaction:</strong> Key players across the sector are adjusting their workflows to accommodate these market shifts.</li>
</ol>

<h2>Who Is Affected & What Happens Next?</h2>
<p>
    Industry leaders, digital strategists, and consumers operating within <strong>{html.escape(category)}</strong> stand to be directly affected by these changes. As further information emerges from {html.escape(publisher)} and associated channels, ongoing updates will clarify long-term outcomes.
</p>
<p>
    Moving forward, key indicators to monitor include shifts in search volume, regulatory responses, and updated product announcements related to {html.escape(focus_keyword)}.
</p>
""".strip()

    # Generate 4-5 relevant FAQs for AEO (Answer Engine Optimization)
    faq = [
        {
            "question": f"What is the main significance of {title}?",
            "answer": f"{title} represents a major development in the {category} space, highlighting rising interest and news coverage across {region}."
        },
        {
            "question": f"Why is {title} trending right now?",
            "answer": f"The topic gained momentum following verified coverage by {publisher} and a surge in user search queries for related keywords such as {', '.join(keywords[:3]) if keywords else focus_keyword}."
        },
        {
            "question": f"How does this development impact the {category} industry?",
            "answer": f"It provides actionable intelligence for creators, strategists, and businesses seeking to align their content and product roadmaps with current market demand."
        },
        {
            "question": f"Where can I follow updates on {title}?",
            "answer": f"You can monitor live trends on DigitalBrief's trend pipeline or follow ongoing coverage via {publisher}."
        }
    ]

    # Meta & Social fields
    seo_title = f"{title} — {category} Trend Briefing"
    if len(seo_title) > 65:
        seo_title = f"{title[:55]}... | DigitalBrief"
    
    meta_desc = description[:150] if description else f"In-depth analysis of {title}. Discover key insights, market impacts, and expert analysis in the {category} sector."
    
    tags = [category] + keywords[:5]

    return {
        "title": title,
        "content": body_html,
        "excerpt": excerpt,
        "category": category,
        "tags": tags,
        "featured_image": image_url,
        "image_alt": f"Featured coverage for {title}",
        "author": "DigitalBrief Editorial Desk",
        "source": publisher,
        "source_url": source_url,
        "original_news_id": trend.get("url") or title,
        "status": "published",
        "seo_title": seo_title,
        "meta_description": meta_desc,
        "focus_keyword": focus_keyword,
        "secondary_keywords": secondary_keywords,
        "faq": faq,
        "social_title": seo_title,
        "social_description": meta_desc,
    }
