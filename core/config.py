"""Core configuration with .env loader."""
import os
from pathlib import Path

# Load .env
_ENV = Path(__file__).resolve().parent.parent / ".env"
if _ENV.exists():
    with open(_ENV, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, _, v = line.partition("=")
                k, v = k.strip(), v.strip()
                if k not in os.environ:
                    os.environ[k] = v

# ---- Server ----
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "8765"))
IS_VERCEL = bool(os.getenv("VERCEL"))

# ---- API Keys ----
MEDIASTACK_KEY = os.getenv("MEDIASTACK_KEY", "")
GNEWS_KEY = os.getenv("GNEWS_KEY", "")
CURRENTS_KEY = os.getenv("CURRENTS_KEY", "")
NEWSAPI_KEY = os.getenv("NEWSAPI_KEY", "")
REDDIT_CLIENT_ID = os.getenv("REDDIT_CLIENT_ID", "")
REDDIT_CLIENT_SECRET = os.getenv("REDDIT_CLIENT_SECRET", "")

# ---- News API Keys (added 2026-08-14) ----
WEBZIO_API_KEY = os.getenv("WEBZIO_API_KEY", "")
APITUBE_API_KEY = os.getenv("APITUBE_API_KEY", "")
THENEWS_API_KEY = os.getenv("THENEWS_API_KEY", "")
NYT_API_KEY = os.getenv("NYT_API_KEY", "")
NYT_APP_ID = os.getenv("NYT_APP_ID", "")
MEDIACLOUD_API_KEY = os.getenv("MEDIACLOUD_API_KEY", "")

# ---- APT Limits ----
MEDIASTACK_LIMIT = 20
GNEWS_LIMIT = 20
CURRENTS_LIMIT = 20

# ---- News API Limits (added 2026-08-14) ----
WEBZIO_LIMIT = 20       # posts per request (Lite plan)
WEBZIO_TIMEOUT = 25
APITUBE_LIMIT = 25      # max per request
APITUBE_TIMEOUT = 25
THENEWS_LIMIT = 25      # free tier max per request
THENEWS_TIMEOUT = 25
NYT_LIMIT = 40          # top stories returned
NYT_TIMEOUT = 25
MEDIACLOUD_LIMIT = 30   # stories per request
MEDIACLOUD_TIMEOUT = 25

# ---- Reddit ----
REDDIT_USER_AGENT = "DigitalBrief/1.0"
REDDIT_SUBREDDITS = [
    "technology", "artificial", "MachineLearning", "startups",
    "business", "worldnews", "gadgets", "programming",
    "Futurology", "science", "IndiaTech"
]

# ---- RSS Feeds ----
# Structured source configuration (single source of truth).
#   name     : display name / publisher attribution
#   url      : RSS/Atom feed URL
#   website  : official website (attribution link)
#   category : default category hint (articles are still auto-categorized)
#   active   : False disables the feed without removing it
#   priority : ordering hint (higher = more important; kept as metadata)
RSS_PER_FEED = 8          # max entries taken per feed per refresh
RSS_TIMEOUT = 20          # seconds per feed before it is skipped

RSS_SOURCES = [
    # ── Technology / startup feeds (existing) ──
    {"name": "TechCrunch", "url": "https://techcrunch.com/feed/",
     "website": "https://techcrunch.com", "category": "Technology", "active": True, "priority": 90},
    {"name": "The Verge", "url": "https://www.theverge.com/rss/index.xml",
     "website": "https://www.theverge.com", "category": "Technology", "active": True, "priority": 88},
    {"name": "Ars Technica", "url": "https://feeds.arstechnica.com/arstechnica/index",
     "website": "https://arstechnica.com", "category": "Technology", "active": True, "priority": 86},
    {"name": "Hacker News", "url": "https://hnrss.org/frontpage",
     "website": "https://news.ycombinator.com", "category": "Technology", "active": True, "priority": 85},
    {"name": "Wired", "url": "https://www.wired.com/feed/rss",
     "website": "https://www.wired.com", "category": "Technology", "active": True, "priority": 84},
    {"name": "MIT Tech Review", "url": "https://www.technologyreview.com/feed/",
     "website": "https://www.technologyreview.com", "category": "Technology", "active": True, "priority": 82},
    {"name": "YourStory", "url": "https://yourstory.com/feed",
     "website": "https://yourstory.com", "category": "Startups & Funding", "active": True, "priority": 80},
    {"name": "Inc42", "url": "https://inc42.com/feed/",
     "website": "https://inc42.com", "category": "Startups & Funding", "active": True, "priority": 80},
    # ── India news feeds (user-provided) ──
    {"name": "BBC India", "url": "https://feeds.bbci.co.uk/news/world/asia/india/rss.xml",
     "website": "https://www.bbc.com/news/world/asia/india", "category": "India News", "active": True, "priority": 85},
    {"name": "The Hindu", "url": "https://www.thehindu.com/feeder/default.rss",
     "website": "https://www.thehindu.com", "category": "India News", "active": True, "priority": 84},
    {"name": "NDTV", "url": "https://feeds.feedburner.com/ndtvnews-top-stories",
     "website": "https://www.ndtv.com", "category": "India News", "active": True, "priority": 84},
    {"name": "India Today", "url": "https://www.indiatoday.in/rss/home",
     "website": "https://www.indiatoday.in", "category": "India News", "active": True, "priority": 82},
    {"name": "Times of India", "url": "https://timesofindia.indiatimes.com/rssfeedstopstories.cms",
     "website": "https://timesofindia.indiatimes.com", "category": "India News", "active": True, "priority": 82},
    {"name": "The Indian Express", "url": "http://indianexpress.com/print/front-page/feed/",
     "website": "https://indianexpress.com", "category": "India News", "active": True, "priority": 80},
    {"name": "ThePrint", "url": "https://theprint.in/feed/",
     "website": "https://theprint.in", "category": "India News", "active": True, "priority": 78},
    {"name": "Hindustan Times", "url": "https://www.hindustantimes.com/feeds/rss/india-news/rssfeed.xml",
     "website": "https://www.hindustantimes.com", "category": "India News", "active": True, "priority": 80},
    {"name": "Business Standard", "url": "https://www.business-standard.com/rss/home_page_top_stories.rss",
     "website": "https://www.business-standard.com", "category": "Business & Finance", "active": True, "priority": 78},
    {"name": "The Guardian India", "url": "https://www.theguardian.com/world/india/rss",
     "website": "https://www.theguardian.com/world/india", "category": "India News", "active": True, "priority": 82},
]

# Flat list kept for backward compatibility with the fetcher signature.
RSS_FEEDS = [(s["name"], s["url"]) for s in RSS_SOURCES if s.get("active", True)]

# ---- News Channels (live news section) ----
#   embed = "youtube" -> iframe via youtube-nocookie live_stream (channel verified embeddable)
#   embed = "link"    -> card with official-site / YouTube buttons (embedding blocked or unsupported)
NEWS_CHANNELS = [
    {"name": "NDTV", "type": "channel", "region": "India",
     "website": "https://www.ndtv.com", "youtube": "UCZFMm1mMw0F81Z37aaEzTUA",
     "embed": "custom", "embedUrl": "https://www.ndtv.com/videos/embed-player/?id=LIVE_BG24x7&mute=1&autostart=1&mutestart=true&pWidth=100&pHeight=100",
     "embedAllow": "autoplay; fullscreen", "active": True, "priority": 95},
    {"name": "BBC News", "type": "channel", "region": "UK",
     "website": "https://www.bbc.com/news", "youtube": "UC16niRr50-MSBwiO3YDb3RA",
     "embed": "youtube", "active": True, "priority": 94},
    {"name": "Al Jazeera English", "type": "channel", "region": "Global",
     "website": "https://www.aljazeera.com/live/", "youtube": "UCNye-wNBqNL5ZzHSJj3l8Bg",
     "embed": "iframely", "iframelyUrl": "https://iframely.net/shq5yDP6?theme=dark",
     "active": True, "priority": 92},
    {"name": "France 24 English", "type": "channel", "region": "France · Global",
     "website": "https://www.france24.com/en/live", "youtube": "UCQfwfsi5VrQ8yKZ-UWmAEFg",
     "embed": "youtube", "active": True, "priority": 90},
    {"name": "DW News", "type": "channel", "region": "Germany · Global",
     "website": "https://www.dw.com/en/top-stories/s-9097", "youtube": "UCknLrEdhRCp1aegoMqRaCZg",
     "embed": "iframely", "iframelyUrl": "https://iframely.net/LF5O0RHg?theme=dark",
     "embedLink": "https://www.dw.com/en/live-tv/channel-english", "active": True, "priority": 90},
    {"name": "WION", "type": "channel", "region": "India · Global",
     "website": "https://www.wionews.com", "youtube": "UC_gUM8rL-Lrg6O3adPW9K1g",
     "embed": "youtube", "active": True, "priority": 88},
    {"name": "India Today", "type": "channel", "region": "India",
     "website": "https://www.indiatoday.in", "youtube": "UCYPvAwZP8pZhSMW8qs7cVCw",
     "embed": "custom", "embedUrl": "https://feeds.intoday.in/livetv/ver-3-0/?id=livetv-it&aud_togle=1&autostart=0&mute=1&t_src=live_tv_page&t_med=web&utm_medium=web&dimlight=1&utm_source=live_tv_page&pip_icon=1&v=1.37&tt=1",
     "active": True, "priority": 86},
    {"name": "The Indian Express", "type": "channel", "region": "India",
     "website": "https://indianexpress.com", "youtube": "UCJEDFSxHHOW1PpBccdSxOTA",
     "embed": "youtube", "active": True, "priority": 82},
    {"name": "News18 India", "type": "channel", "region": "India",
     "website": "https://www.news18.com", "youtube": "UCPP3etACgdUWvizcES1dJ8Q",
     "embed": "youtube", "active": True, "priority": 82},
    {"name": "Euronews", "type": "channel", "region": "Europe · Global",
     "website": "https://www.euronews.com", "youtube": "UCSrZ3UV4jOidv8ppoVuvW9Q",
     "embed": "youtube", "active": True, "priority": 80},
    {"name": "Sky News", "type": "channel", "region": "UK",
     "website": "https://news.sky.com", "youtube": "UCoMdktPbSTixAyNGwb-UYkQ",
     "embed": "custom", "embedUrl": "https://www.youtube.com/embed/YDvsBbKfLPA?rel=0",
     "embedAllow": "accelerometer *; clipboard-write *; encrypted-media *; gyroscope *; picture-in-picture *; web-share *;", "active": True, "priority": 76},
    {"name": "Reuters", "type": "channel", "region": "Global",
     "website": "https://www.reuters.com", "youtube": "UChqUTb7kYRX8-EiaN3XFrSQ",
     "embed": "link", "active": True, "priority": 74,
     "note": "Reuters video is licensed — watch on the official site or YouTube."},
    {"name": "Times of India", "type": "channel", "region": "India",
     "website": "https://timesofindia.indiatimes.com", "youtube": "",
     "embed": "link", "active": True, "priority": 72,
     "note": "Times of India offers RSS headlines (integrated above) — visit the official site."},
]

# ---- Google Trends ----
GOOGLE_TRENDS_PROXY = os.getenv("GT_PROXY")
CONTENT_KEYWORDS = [
    "AI tools", "artificial intelligence", "chatgpt", "machine learning",
    "openai", "data science", "cybersecurity", "startup funding",
    "crypto", "blockchain", "fintech", "SEO", "web development",
    "digital marketing", "wordpress", "remote work", "ecommerce"
]

# ---- Aggregator ----
TREND_SCORE_WEIGHTS = {
    "rss": 40, "gnews": 38, "mediastack": 36, "newsapi": 35,
    "currents": 34, "reddit": 32, "google_trends": 12,
    # Added 2026-08-14: five new news APIs
    "webzio": 36, "thenewsapi": 35, "apitube": 34, "nytimes": 33,
    "mediacloud": 30,
}
MULTI_SOURCE_BONUS = 25
MAX_TRENDS = 250
REFRESH_INTERVAL_MINUTES = 30
