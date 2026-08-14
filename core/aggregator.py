"""Trend Aggregator — merge, dedup, score, and generate content ideas."""
import logging
from difflib import SequenceMatcher
from urllib.parse import quote, urlparse

logger = logging.getLogger("trends.aggregator")

# Max bonus a trend can accumulate from being seen in multiple sources
# (unbounded stacking previously let a 5-source wire story lock rank #1).
MAX_BONUS = 50


def _search_url(title):
    """Fallback URL: Google search for the trend title."""
    return f"https://www.google.com/search?q={quote(title)}"


def _ensure_url(title, url):
    """Return a non-empty, clickable URL for every trend."""
    u = (url or "").strip()
    if u and u not in ("#", "/"):
        return u
    return _search_url(title)


def _url_key(url):
    """Normalized identity key for exact-URL dedup (scheme+host+path)."""
    try:
        p = urlparse(url)
        return (p.scheme.lower(), p.netloc.lower(), p.path.rstrip("/"))
    except Exception:
        return ("", "", url)


class TrendAggregator:
    def __init__(self, weights, multi_bonus=25, max_trends=150):
        self.weights = weights
        self.bonus = multi_bonus
        self.max_trends = max_trends

    def merge_and_score(self, sources):
        """Merge trends from multiple sources, deduplicate, and rank."""
        all_trends = []

        for source_name, trends in sources.items():
            weight = self.weights.get(source_name, 15)
            for t in trends:
                title = t.get("title", "").strip()
                if not title or len(title) < 5:
                    continue
                score = weight
                score += min(t.get("score", 0) // 10, 30)
                score += min(t.get("num_comments", 0), 20)
                all_trends.append({
                    "title": title,
                    "url": _ensure_url(title, t.get("url", "")),
                    "source": source_name,
                    "description": t.get("description", ""),
                    "published_at": t.get("published_at", ""),
                    "base_score": score,
                    "bonus": 0,
                    "subreddit": t.get("subreddit"),
                    "raw_data": {k: v for k, v in t.items()
                                 if k not in ("title", "url", "source",
                                              "description", "published_at", "subreddit")},
                })

        # Deduplicate: exact normalized-URL pass first, then fuzzy title match
        # (only for comparable title lengths to avoid false merges).
        merged, seen = [], []
        url_index = {}
        for trend in all_trends:
            t = trend["title"].lower()
            dup = False
            best = -1
            key = _url_key(trend["url"])
            if key[2] and key in url_index:
                best = url_index[key]
                dup = True
            if not dup:
                for i, s in enumerate(seen):
                    if abs(len(t) - len(s)) / max(len(t), len(s), 1) > 0.45:
                        continue  # title lengths too different to be the same story
                    if SequenceMatcher(None, t, s).ratio() > 0.78:
                        dup = True
                        best = i
                        break
            if dup and best >= 0:
                m = merged[best]
                m["bonus"] = min(m["bonus"] + self.bonus, MAX_BONUS)
                m["sources"] = list(set(
                    m.get("sources", [m["source"]]) + [trend["source"]]
                ))
                url_index[key] = best
            else:
                seen.append(t)
                trend["sources"] = [trend["source"]]
                merged.append(trend)
                url_index[key] = len(merged) - 1

        # Score first, then recency (newer wins ties) — keeps fresh items visible
        merged.sort(key=lambda x: (x["base_score"] + x["bonus"], x.get("published_at") or ""),
                    reverse=True)
        for i, m in enumerate(merged[:self.max_trends]):
            m["rank"] = i + 1
            m["trend_score"] = min(100, m["base_score"] + m["bonus"])

        result = merged[:self.max_trends]
        logger.info(f"Aggregated: {len(all_trends)} raw -> {len(result)} unique")
        return result


class TrendSummary:
    """Generate summaries and content ideas from trend data."""

    @staticmethod
    def top_rising(trends, n=10):
        return [
            {"rank": t["rank"], "title": t["title"],
             "score": t["trend_score"],
             "sources": t.get("sources", [t["source"]])}
            for t in trends[:n]
        ]

    @staticmethod
    def content_ideas(trends, min_score=50):
        ideas = []
        for t in trends:
            if t["trend_score"] >= min_score:
                ideas.append({
                    "title": t["title"],
                    "score": t["trend_score"],
                    "category": _guess_category(t),
                    "sources": t.get("sources", []),
                    "angles": [
                        f"What {t['title']} means for the industry",
                        f"How {t['title']} is reshaping the market",
                        f"5 key takeaways from {t['title']}",
                    ],
                })
        return ideas


def _guess_category(trend):
    title = trend.get("title", "").lower()
    if any(k in title for k in ["ai ", "artificial", "chatgpt", "openai", "llm", "machine learning"]):
        return "AI"
    if any(k in title for k in ["startup", "funding", "venture", "ipo", "series "]):
        return "Startups"
    if any(k in title for k in ["crypto", "bitcoin", "blockchain", "web3"]):
        return "Crypto"
    if any(k in title for k in ["seo", "marketing", "social media"]):
        return "Marketing"
    if any(k in title for k in ["security", "cyber", "breach", "hack"]):
        return "Security"
    if any(k in title for k in ["developer", "code", "programming", "web dev"]):
        return "Development"
    return "Technology"
