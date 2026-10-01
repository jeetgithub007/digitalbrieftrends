"""Article storage module — thread-safe JSON-backed persistence for published and draft articles."""
import os
import json
import time
import threading
import logging
import re
from pathlib import Path
from datetime import datetime, timezone

logger = logging.getLogger("trends.articles")

# Default file location in root directory
ROOT = Path(__file__).resolve().parent.parent
ARTICLES_FILE = ROOT / "published_articles.json"


def slugify(text):
    """Generate a clean, SEO-friendly URL slug from text."""
    if not text:
        return f"article-{int(time.time())}"
    text = text.lower().strip()
    # Replace non-alphanumeric with hyphen
    slug = re.sub(r"[^\w\s-]", "", text)
    slug = re.sub(r"[\s_-]+", "-", slug).strip("-")
    return slug[:80] or f"article-{int(time.time())}"


class ArticleStore:
    def __init__(self, filepath=ARTICLES_FILE):
        self.filepath = filepath
        self._lock = threading.Lock()
        self._articles = []
        self._load()

    def _load(self):
        with self._lock:
            if self.filepath.exists():
                try:
                    with open(self.filepath, encoding="utf-8") as f:
                        self._articles = json.load(f)
                    logger.info(f"Loaded {len(self._articles)} articles from {self.filepath.name}")
                except Exception as e:
                    logger.error(f"Failed to load articles file: {e}")
                    self._articles = []
            else:
                self._articles = []
                self._save_locked()
        
        # Purge articles older than 30 days unless updated
        self.clean_expired_articles(max_age_days=30)

    def clean_expired_articles(self, max_age_days=30):
        """Purge articles older than max_age_days. Updating an article extends its retention."""
        with self._lock:
            now_ts = time.time()
            cutoff_sec = max_age_days * 86400
            initial_count = len(self._articles)
            
            valid_articles = []
            for a in self._articles:
                date_str = a.get("updated_at") or a.get("published_at") or a.get("created_at")
                art_ts = now_ts
                if date_str:
                    try:
                        # Parse ISO 8601 string
                        clean_str = date_str.replace("Z", "+00:00")
                        dt = datetime.fromisoformat(clean_str)
                        art_ts = dt.timestamp()
                    except Exception:
                        art_ts = now_ts

                if (now_ts - art_ts) <= cutoff_sec:
                    valid_articles.append(a)

            if len(valid_articles) < initial_count:
                purged_count = initial_count - len(valid_articles)
                self._articles = valid_articles
                self._save_locked()
                logger.info(f"Purged {purged_count} expired article(s) older than {max_age_days} days.")


    def _save_locked(self):
        try:
            temp_path = self.filepath.with_suffix(".tmp")
            with open(temp_path, "w", encoding="utf-8") as f:
                json.dump(self._articles, f, indent=2, ensure_ascii=False)
            temp_path.replace(self.filepath)
        except Exception as e:
            logger.error(f"Failed to save articles file: {e}")

    def list_articles(self, status=None, category=None, search=None, limit=50, offset=0):
        with self._lock:
            items = list(self._articles)

        if status:
            items = [a for a in items if a.get("status") == status]

        if category:
            c_norm = category.lower().strip()
            items = [a for a in items if (a.get("category") or "").lower().strip() == c_norm]

        if search:
            q = search.lower().strip()
            items = [a for a in items if q in (a.get("title") or "").lower() or q in (a.get("content") or "").lower() or q in (a.get("excerpt") or "").lower()]

        # Sort newest first
        items.sort(key=lambda a: a.get("published_at") or a.get("created_at") or "", reverse=True)
        total = len(items)
        paginated = items[offset : offset + limit]
        return paginated, total

    def get_by_id(self, article_id):
        with self._lock:
            for a in self._articles:
                if str(a.get("id")) == str(article_id):
                    return dict(a)
        return None

    def get_by_slug(self, slug):
        if not slug:
            return None
        slug_norm = slug.lower().strip()
        with self._lock:
            for a in self._articles:
                if (a.get("slug") or "").lower().strip() == slug_norm:
                    return dict(a)
        return None

    def get_by_news_id(self, news_id):
        """Find an article already generated from a specific news card title/URL."""
        if not news_id:
            return None
        n_norm = str(news_id).lower().strip()
        with self._lock:
            for a in self._articles:
                if str(a.get("original_news_id", "")).lower().strip() == n_norm:
                    return dict(a)
        return None

    def create(self, data):
        with self._lock:
            now_iso = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
            art_id = f"art_{int(time.time() * 1000)}"

            title = (data.get("title") or "Untitled Article").strip()
            base_slug = slugify(data.get("slug") or title)

            # Ensure unique slug
            slug = base_slug
            counter = 1
            existing_slugs = { (a.get("slug") or "").lower() for a in self._articles }
            while slug.lower() in existing_slugs:
                slug = f"{base_slug}-{counter}"
                counter += 1

            # Estimate reading time (approx 200 words/min)
            word_count = len((data.get("content") or "").split())
            read_time = max(1, round(word_count / 200))

            article = {
                "id": art_id,
                "title": title,
                "slug": slug,
                "content": data.get("content", ""),
                "excerpt": data.get("excerpt", ""),
                "category": data.get("category", "Technology"),
                "tags": data.get("tags", []),
                "featured_image": data.get("featured_image", ""),
                "image_alt": data.get("image_alt") or title,
                "author": data.get("author") or "DigitalBrief Editorial Desk",
                "source": data.get("source", ""),
                "source_url": data.get("source_url", ""),
                "original_news_id": data.get("original_news_id", ""),
                "status": data.get("status", "published"),
                "published_at": data.get("published_at") or now_iso,
                "created_at": now_iso,
                "updated_at": now_iso,
                "seo_title": data.get("seo_title") or title,
                "meta_description": data.get("meta_description") or data.get("excerpt", "")[:155],
                "focus_keyword": data.get("focus_keyword", ""),
                "secondary_keywords": data.get("secondary_keywords", []),
                "faq": data.get("faq", []),
                "social_title": data.get("social_title") or data.get("seo_title") or title,
                "social_description": data.get("social_description") or data.get("meta_description", ""),
                "read_time_minutes": read_time,
            }

            self._articles.append(article)
            self._save_locked()
            logger.info(f"Created article #{art_id}: '{title}' (slug: {slug})")
            return dict(article)

    def update(self, article_id, updates):
        with self._lock:
            for idx, a in enumerate(self._articles):
                if str(a.get("id")) == str(article_id):
                    now_iso = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

                    # Handle slug uniqueness if slug changed
                    new_slug = updates.get("slug")
                    if new_slug and new_slug != a.get("slug"):
                        base_slug = slugify(new_slug)
                        slug = base_slug
                        counter = 1
                        existing_slugs = { (art.get("slug") or "").lower() for i, art in enumerate(self._articles) if i != idx }
                        while slug.lower() in existing_slugs:
                            slug = f"{base_slug}-{counter}"
                            counter += 1
                        updates["slug"] = slug

                    # Update word count and read time if content changed
                    if "content" in updates:
                        word_count = len((updates["content"] or "").split())
                        updates["read_time_minutes"] = max(1, round(word_count / 200))

                    updates["updated_at"] = now_iso

                    # Merge updates
                    a.update(updates)
                    self._articles[idx] = a
                    self._save_locked()
                    logger.info(f"Updated article #{article_id}: '{a.get('title')}'")
                    return dict(a)
        return None

    def delete(self, article_id):
        with self._lock:
            initial_len = len(self._articles)
            self._articles = [a for a in self._articles if str(a.get("id")) != str(article_id)]
            if len(self._articles) < initial_len:
                self._save_locked()
                logger.info(f"Deleted article #{article_id}")
                return True
        return False


# Global article store instance
article_store = ArticleStore()
