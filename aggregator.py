"""
Trend Aggregator — merges, deduplicates, scores, and ranks trends from all sources.
"""
import logging
from difflib import SequenceMatcher

logger = logging.getLogger("trend-pipeline.aggregator")

class TrendAggregator:
    def __init__(self, weights, multi_source_bonus=25, max_trends=100):
        self.weights = weights
        self.multi_source_bonus = multi_source_bonus
        self.max_trends = max_trends

    def merge_and_score(self, trends_by_source):
        """
        Accept: {
            "google_trends": [...],
            "newsapi": [...],
            "reddit": [...],
            "rss": [...]
        }
        Return: unified, deduplicated, ranked list of trends.
        """
        all_trends = []

        for source, trends in trends_by_source.items():
            weight = self.weights.get(source, 15)
            for t in trends:
                title = t.get("title", t.get("query", "")).strip()
                if not title or len(title) < 5:
                    continue

                score = weight
                # Social proof boost
                score += min(t.get("score", 0) // 10, 30)
                # Comment engagement boost
                score += min(t.get("num_comments", 0), 20)
                # Google search volume boost (regional score mappings)
                if "search_volume" in t:
                    score += min(t["search_volume"] // 100, 25)

                all_trends.append({
                    "title": title,
                    "url": t.get("url", ""),
                    "source": source,
                    "description": t.get("description", ""),
                    "subreddit": t.get("subreddit"),
                    "published_at": t.get("published_at", ""),
                    "base_score": score,
                    "raw_data": {k: v for k, v in t.items()
                                 if k not in ("title", "url", "source", "description",
                                               "subreddit", "published_at")},
                })

        # Deduplicate & boost multi-source
        merged = []
        seen = []

        for trend in all_trends:
            title = trend["title"].lower()
            is_dup = False
            max_sim = 0
            best_match_idx = -1

            for i, seen_title in enumerate(seen):
                sim = SequenceMatcher(None, title, seen_title).ratio()
                if sim > max_sim:
                    max_sim = sim
                    best_match_idx = i
                if sim > 0.78:
                    is_dup = True
                    break

            if is_dup and best_match_idx >= 0:
                # Boost existing entry — it appeared from multiple sources
                merged[best_match_idx]["base_score"] += self.multi_source_bonus
                merged[best_match_idx]["sources"] = list(set(
                    merged[best_match_idx].get("sources", [merged[best_match_idx]["source"]]) + [trend["source"]]
                ))
                if trend["url"] and not merged[best_match_idx]["url"]:
                    merged[best_match_idx]["url"] = trend["url"]
            else:
                seen.append(title)
                trend["sources"] = [trend["source"]]
                merged.append(trend)

        # Sort by score descending
        merged.sort(key=lambda x: x["base_score"], reverse=True)

        # Assign rank and trend_score (normalized 0-100)
        for i, trend in enumerate(merged[:self.max_trends]):
            trend["rank"] = i + 1
            trend["trend_score"] = min(100, trend["base_score"])

        result = merged[:self.max_trends]

        # Source distribution summary
        source_counts = {}
        for t in result:
            for s in t.get("sources", [t["source"]]):
                source_counts[s] = source_counts.get(s, 0) + 1

        logger.info(
            f"Aggregated: {len(all_trends)} raw → {len(result)} unique trends. "
            f"Sources: {source_counts}"
        )
        return result


class TrendSummary:
    """Generate human-readable summaries of trend data."""

    @staticmethod
    def top_rising(trends, n=10):
        """Top N rising trends for quick display."""
        return [
            {
                "rank": t["rank"],
                "title": t["title"],
                "score": t["trend_score"],
                "sources": t.get("sources", [t["source"]]),
            }
            for t in trends[:n]
        ]

    @staticmethod
    def by_source(trends, source):
        """Filter trends by source."""
        return [t for t in trends if t["source"] == source or source in t.get("sources", [])]

    @staticmethod
    def content_ideas(trends, min_score=50):
        """High-scoring trends suitable for article ideas."""
        ideas = []
        for t in trends:
            if t["trend_score"] >= min_score:
                ideas.append({
                    "title": t["title"],
                    "score": t["trend_score"],
                    "angle_suggestions": [
                        f"What is {t['title']} and why it matters",
                        f"How {t['title']} is changing the industry",
                        f"Top 5 things to know about {t['title']}",
                    ],
                    "sources": t.get("sources", []),
                    "category": TrendSummary._guess_category(t),
                })
        return ideas

    @staticmethod
    def _guess_category(trend):
        """Guess topic category from keywords."""
        title = trend.get("title", "").lower()
        sources = trend.get("sources", [])
        if any(k in title for k in ["ai ", "artificial", "chatgpt", "openai", "machine learning", "llm"]):
            return "AI"
        if any(k in title for k in ["startup", "funding", "venture", "series ", "ipo"]):
            return "Startups"
        if any(k in title for k in ["crypto", "bitcoin", "blockchain", "web3"]):
            return "Crypto"
        if any(k in title for k in ["seo", "marketing", "social media", "content"]):
            return "Digital Marketing"
        if any(k in title for k in ["security", "cyber", "hack", "breach"]):
            return "Cybersecurity"
        if any(k in title for k in ["web dev", "programming", "code", "developer"]):
            return "Development"
        return "Technology"
