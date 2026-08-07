"""
Trend Pipeline Configuration
API keys loaded from environment variables.
Copy .env.example to .env and fill in your keys.
"""
import os
from pathlib import Path

# Load .env file if it exists (no extra dependency needed)
_ENV_PATH = Path(__file__).parent / ".env"
if _ENV_PATH.exists():
    with open(_ENV_PATH, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, _, val = line.partition("=")
                key, val = key.strip(), val.strip()
                if key not in os.environ:
                    os.environ[key] = val

# ---- Server ----
HOST = os.getenv("TREND_HOST", "0.0.0.0")
PORT = int(os.getenv("TREND_PORT", "8765"))

# ---- Google Trends (pytrends) ----
GOOGLE_TRENDS_PROXY = os.getenv("GT_PROXY", None)

# ===== NEWS APIS =====

# NewsAPI.org
NEWSAPI_KEY = os.getenv("NEWSAPI_KEY", "")
NEWSAPI_COUNTRY = os.getenv("NEWSAPI_COUNTRY", "in")
NEWSAPI_CATEGORIES = ["technology", "business", "science"]

# Mediastack
MEDIASTACK_KEY = os.getenv("MEDIASTACK_KEY", "035b95516d0ca390ed89a98e821d894c")
MEDIASTACK_COUNTRIES = "in,us"
MEDIASTACK_CATEGORIES = "technology,business,science"
MEDIASTACK_LIMIT = 20

# GNews
GNEWS_KEY = os.getenv("GNEWS_KEY", "50ebe5ba94569ad62ea847d35c77a738")
GNEWS_COUNTRY = "in"
GNEWS_LIMIT = 20

# Currents API
CURRENTS_KEY = os.getenv("CURRENTS_KEY", "XdnezcX_9rmyqBKrE9ZnSGZC2urbOaD3A1eACV-_k2vhyorM")
CURRENTS_CATEGORIES = ["technology", "business", "science", "AI"]
CURRENTS_LIMIT = 20

# ---- Reddit ----
REDDIT_CLIENT_ID = os.getenv("REDDIT_CLIENT_ID", "")
REDDIT_CLIENT_SECRET = os.getenv("REDDIT_CLIENT_SECRET", "")
REDDIT_USER_AGENT = os.getenv("REDDIT_USER_AGENT", "DigitalBrief/1.0")
REDDIT_SUBREDDITS = [
    "technology", "artificial", "MachineLearning", "startups",
    "business", "worldnews", "gadgets", "programming", "webdev",
    "Futurology", "science", "IndiaTech"
]

# ---- RSS Feeds ----
RSS_FEEDS = [
    ("TechCrunch", "https://techcrunch.com/feed/"),
    ("The Verge", "https://www.theverge.com/rss/index.xml"),
    ("Ars Technica", "https://feeds.arstechnica.com/arstechnica/index"),
    ("Hacker News", "https://hnrss.org/frontpage"),
    ("Wired", "https://www.wired.com/feed/rss"),
    ("MIT Tech Review", "https://www.technologyreview.com/feed/"),
    ("YourStory", "https://yourstory.com/feed"),
    ("Inc42", "https://inc42.com/feed/"),
]

# ---- Aggregator ----
TREND_SCORE_WEIGHTS = {
    "google_trends": 30,
    "newsapi": 30,
    "mediastack": 32,
    "gnews": 35,
    "currents": 33,
    "reddit": 35,
    "rss": 20,
}
MULTI_SOURCE_BONUS = 25
MAX_TRENDS = 150
REFRESH_INTERVAL_MINUTES = 30

# ---- Content Keywords (Google Trends) ----
CONTENT_KEYWORDS = [
    "AI tools", "artificial intelligence", "chatgpt", "machine learning",
    "openai", "google AI", "data science", "cybersecurity",
    "startup funding", "crypto", "blockchain", "fintech",
    "SEO", "web development", "digital marketing", "wordpress",
    "content marketing", "remote work", "ecommerce", "cloud computing"
]
