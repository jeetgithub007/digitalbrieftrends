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
    {
        "name": "BBC News",
        "url": "https://feeds.bbci.co.uk/news/rss.xml",
        "website": "https://feeds.bbci.co.uk",
        "category": "World News",
        "active": True,
        "priority": 80
    },
    {
        "name": "BBC World",
        "url": "https://feeds.bbci.co.uk/news/world/rss.xml",
        "website": "https://feeds.bbci.co.uk",
        "category": "World News",
        "active": True,
        "priority": 80
    },
    {
        "name": "BBC Asia",
        "url": "https://feeds.bbci.co.uk/news/world/asia/rss.xml",
        "website": "https://feeds.bbci.co.uk",
        "category": "World News",
        "active": True,
        "priority": 80
    },
    {
        "name": "BBC Europe",
        "url": "https://feeds.bbci.co.uk/news/world/europe/rss.xml",
        "website": "https://feeds.bbci.co.uk",
        "category": "World News",
        "active": True,
        "priority": 80
    },
    {
        "name": "BBC Middle East",
        "url": "https://feeds.bbci.co.uk/news/world/middle_east/rss.xml",
        "website": "https://feeds.bbci.co.uk",
        "category": "World News",
        "active": True,
        "priority": 80
    },
    {
        "name": "BBC Africa",
        "url": "https://feeds.bbci.co.uk/news/world/africa/rss.xml",
        "website": "https://feeds.bbci.co.uk",
        "category": "World News",
        "active": True,
        "priority": 80
    },
    {
        "name": "BBC India",
        "url": "https://feeds.bbci.co.uk/news/world/asia/india/rss.xml",
        "website": "https://feeds.bbci.co.uk",
        "category": "India News",
        "active": True,
        "priority": 80
    },
    {
        "name": "CNN Top Stories",
        "url": "http://rss.cnn.com/rss/cnn_topstories.rss",
        "website": "https://rss.cnn.com",
        "category": "World News",
        "active": True,
        "priority": 80
    },
    {
        "name": "CNN World",
        "url": "http://rss.cnn.com/rss/edition_world.rss",
        "website": "https://rss.cnn.com",
        "category": "World News",
        "active": True,
        "priority": 80
    },
    {
        "name": "CNN U.S.",
        "url": "http://rss.cnn.com/rss/cnn_us.rss",
        "website": "https://rss.cnn.com",
        "category": "World News",
        "active": True,
        "priority": 80
    },
    {
        "name": "CNN Business",
        "url": "http://rss.cnn.com/rss/money_latest.rss",
        "website": "https://rss.cnn.com",
        "category": "Business & Finance",
        "active": True,
        "priority": 80
    },
    {
        "name": "Al Jazeera English",
        "url": "https://www.aljazeera.com/xml/rss/all.xml",
        "website": "https://www.aljazeera.com",
        "category": "World News",
        "active": True,
        "priority": 80
    },
    {
        "name": "The Guardian World",
        "url": "https://www.theguardian.com/world/rss",
        "website": "https://www.theguardian.com",
        "category": "World News",
        "active": True,
        "priority": 80
    },
    {
        "name": "The Guardian Politics",
        "url": "https://www.theguardian.com/politics/rss",
        "website": "https://www.theguardian.com",
        "category": "Politics",
        "active": True,
        "priority": 80
    },
    {
        "name": "The Guardian Technology",
        "url": "https://www.theguardian.com/uk/technology/rss",
        "website": "https://www.theguardian.com",
        "category": "Technology",
        "active": True,
        "priority": 80
    },
    {
        "name": "The Guardian Environment",
        "url": "https://www.theguardian.com/environment/rss",
        "website": "https://www.theguardian.com",
        "category": "Energy & Climate",
        "active": True,
        "priority": 80
    },
    {
        "name": "The New York Times Home",
        "url": "https://rss.nytimes.com/services/xml/rss/nyt/HomePage.xml",
        "website": "https://rss.nytimes.com",
        "category": "World News",
        "active": True,
        "priority": 80
    },
    {
        "name": "NYT World",
        "url": "https://rss.nytimes.com/services/xml/rss/nyt/World.xml",
        "website": "https://rss.nytimes.com",
        "category": "World News",
        "active": True,
        "priority": 80
    },
    {
        "name": "NYT U.S.",
        "url": "https://rss.nytimes.com/services/xml/rss/nyt/US.xml",
        "website": "https://rss.nytimes.com",
        "category": "World News",
        "active": True,
        "priority": 80
    },
    {
        "name": "NYT Politics",
        "url": "https://rss.nytimes.com/services/xml/rss/nyt/Politics.xml",
        "website": "https://rss.nytimes.com",
        "category": "Politics",
        "active": True,
        "priority": 80
    },
    {
        "name": "NYT Technology",
        "url": "https://rss.nytimes.com/services/xml/rss/nyt/Technology.xml",
        "website": "https://rss.nytimes.com",
        "category": "Technology",
        "active": True,
        "priority": 80
    },
    {
        "name": "NPR News",
        "url": "https://feeds.npr.org/1001/rss.xml",
        "website": "https://feeds.npr.org",
        "category": "World News",
        "active": True,
        "priority": 80
    },
    {
        "name": "NPR World",
        "url": "https://feeds.npr.org/1004/rss.xml",
        "website": "https://feeds.npr.org",
        "category": "World News",
        "active": True,
        "priority": 80
    },
    {
        "name": "NPR Politics",
        "url": "https://feeds.npr.org/1014/rss.xml",
        "website": "https://feeds.npr.org",
        "category": "Politics",
        "active": True,
        "priority": 80
    },
    {
        "name": "NPR Technology",
        "url": "https://feeds.npr.org/1019/rss.xml",
        "website": "https://feeds.npr.org",
        "category": "Technology",
        "active": True,
        "priority": 80
    },
    {
        "name": "Deutsche Welle",
        "url": "https://rss.dw.com/xml/rss-en-all",
        "website": "https://rss.dw.com",
        "category": "World News",
        "active": True,
        "priority": 80
    },
    {
        "name": "France 24 English",
        "url": "https://www.france24.com/en/rss",
        "website": "https://www.france24.com",
        "category": "World News",
        "active": True,
        "priority": 80
    },
    {
        "name": "Sky News",
        "url": "https://feeds.skynews.com/feeds/rss/home.xml",
        "website": "https://feeds.skynews.com",
        "category": "World News",
        "active": True,
        "priority": 80
    },
    {
        "name": "NBC News Top Stories",
        "url": "https://feeds.nbcnews.com/feeds/topstories",
        "website": "https://feeds.nbcnews.com",
        "category": "World News",
        "active": True,
        "priority": 80
    },
    {
        "name": "NBC News World",
        "url": "https://feeds.nbcnews.com/feeds/worldnews",
        "website": "https://feeds.nbcnews.com",
        "category": "World News",
        "active": True,
        "priority": 80
    },
    {
        "name": "Time",
        "url": "https://time.com/feed/",
        "website": "https://time.com",
        "category": "World News",
        "active": True,
        "priority": 80
    },
    {
        "name": "The Independent",
        "url": "https://www.independent.co.uk/rss",
        "website": "https://www.independent.co.uk",
        "category": "World News",
        "active": True,
        "priority": 80
    },
    {
        "name": "The Hill",
        "url": "https://thehill.com/homenews/feed/",
        "website": "https://thehill.com",
        "category": "Politics",
        "active": True,
        "priority": 80
    },
    {
        "name": "Vox World Politics",
        "url": "https://www.vox.com/rss/world-politics/index.xml",
        "website": "https://www.vox.com",
        "category": "World News",
        "active": True,
        "priority": 80
    },
    {
        "name": "Christian Science Monitor",
        "url": "https://rss.csmonitor.com/feeds/world",
        "website": "https://rss.csmonitor.com",
        "category": "World News",
        "active": True,
        "priority": 80
    },
    {
        "name": "Google News World",
        "url": "https://news.google.com/rss/headlines/section/topic/WORLD?hl=en-US&gl=US&ceid=US:en",
        "website": "https://news.google.com",
        "category": "World News",
        "active": True,
        "priority": 80
    },
    {
        "name": "Google News Business",
        "url": "https://news.google.com/rss/headlines/section/topic/BUSINESS?hl=en-US&gl=US&ceid=US:en",
        "website": "https://news.google.com",
        "category": "Business & Finance",
        "active": True,
        "priority": 80
    },
    {
        "name": "Google News Technology",
        "url": "https://news.google.com/rss/headlines/section/topic/TECHNOLOGY?hl=en-US&gl=US&ceid=US:en",
        "website": "https://news.google.com",
        "category": "Technology",
        "active": True,
        "priority": 80
    },
    {
        "name": "Google News India",
        "url": "https://news.google.com/rss/headlines/section/geo/India?hl=en-IN&gl=IN&ceid=IN:en",
        "website": "https://news.google.com",
        "category": "India News",
        "active": True,
        "priority": 80
    },
    {
        "name": "Google News Japan",
        "url": "https://news.google.com/rss/headlines/section/geo/Japan?hl=en&gl=JP&ceid=JP:en",
        "website": "https://news.google.com",
        "category": "World News",
        "active": True,
        "priority": 80
    },
    {
        "name": "Google News Reuters Search",
        "url": "https://news.google.com/rss/search?q=site%3Areuters.com&hl=en-US&gl=US&ceid=US:en",
        "website": "https://news.google.com",
        "category": "World News",
        "active": True,
        "priority": 80
    },
    {
        "name": "Yahoo World News",
        "url": "https://rss.news.yahoo.com/rss/world",
        "website": "https://rss.news.yahoo.com",
        "category": "World News",
        "active": True,
        "priority": 80
    },
    {
        "name": "Yahoo U.S. News",
        "url": "https://news.yahoo.com/rss/us",
        "website": "https://news.yahoo.com",
        "category": "World News",
        "active": True,
        "priority": 80
    },
    {
        "name": "AllAfrica",
        "url": "https://allafrica.com/tools/headlines/rdf/latest/headlines.rdf",
        "website": "https://allafrica.com",
        "category": "World News",
        "active": True,
        "priority": 80
    },
    {
        "name": "TASS",
        "url": "https://tass.com/rss/v2.xml",
        "website": "https://tass.com",
        "category": "World News",
        "active": True,
        "priority": 80
    },
    {
        "name": "RT",
        "url": "https://www.rt.com/rss/",
        "website": "https://www.rt.com",
        "category": "World News",
        "active": True,
        "priority": 80
    },
    {
        "name": "Meduza",
        "url": "https://meduza.io/rss/all",
        "website": "https://meduza.io",
        "category": "World News",
        "active": True,
        "priority": 80
    },
    {
        "name": "Euronews",
        "url": "https://www.euronews.com/rss",
        "website": "https://www.euronews.com",
        "category": "World News",
        "active": True,
        "priority": 80
    },
    {
        "name": "The Hindu",
        "url": "https://www.thehindu.com/feeder/default.rss",
        "website": "https://www.thehindu.com",
        "category": "India News",
        "active": True,
        "priority": 80
    },
    {
        "name": "The Hindu National",
        "url": "https://www.thehindu.com/news/national/feeder/default.rss",
        "website": "https://www.thehindu.com",
        "category": "India News",
        "active": True,
        "priority": 80
    },
    {
        "name": "The Hindu International",
        "url": "https://www.thehindu.com/news/international/feeder/default.rss",
        "website": "https://www.thehindu.com",
        "category": "World News",
        "active": True,
        "priority": 80
    },
    {
        "name": "The Hindu Technology",
        "url": "https://www.thehindu.com/sci-tech/technology/feeder/default.rss",
        "website": "https://www.thehindu.com",
        "category": "Technology",
        "active": True,
        "priority": 80
    },
    {
        "name": "Times of India Top Stories",
        "url": "https://timesofindia.indiatimes.com/rssfeedstopstories.cms",
        "website": "https://timesofindia.indiatimes.com",
        "category": "India News",
        "active": True,
        "priority": 80
    },
    {
        "name": "Times of India India",
        "url": "https://timesofindia.indiatimes.com/rssfeeds/-2128936835.cms",
        "website": "https://timesofindia.indiatimes.com",
        "category": "India News",
        "active": True,
        "priority": 80
    },
    {
        "name": "Times of India World",
        "url": "https://timesofindia.indiatimes.com/rssfeeds/296589292.cms",
        "website": "https://timesofindia.indiatimes.com",
        "category": "World News",
        "active": True,
        "priority": 80
    },
    {
        "name": "NDTV Top Stories",
        "url": "https://feeds.feedburner.com/ndtvnews-top-stories",
        "website": "https://feeds.feedburner.com",
        "category": "India News",
        "active": True,
        "priority": 80
    },
    {
        "name": "NDTV World",
        "url": "https://feeds.feedburner.com/ndtvnews-world-news",
        "website": "https://feeds.feedburner.com",
        "category": "World News",
        "active": True,
        "priority": 80
    },
    {
        "name": "NDTV Business",
        "url": "https://feeds.feedburner.com/ndtvprofit-latest",
        "website": "https://feeds.feedburner.com",
        "category": "Business & Finance",
        "active": True,
        "priority": 80
    },
    {
        "name": "News18 World",
        "url": "https://www.news18.com/rss/world.xml",
        "website": "https://www.news18.com",
        "category": "World News",
        "active": True,
        "priority": 80
    },
    {
        "name": "News18 India",
        "url": "https://www.news18.com/rss/india.xml",
        "website": "https://www.news18.com",
        "category": "India News",
        "active": True,
        "priority": 80
    },
    {
        "name": "News18 Technology",
        "url": "https://www.news18.com/rss/tech.xml",
        "website": "https://www.news18.com",
        "category": "Technology",
        "active": True,
        "priority": 80
    },
    {
        "name": "Indian Express",
        "url": "https://indianexpress.com/feed/",
        "website": "https://indianexpress.com",
        "category": "India News",
        "active": True,
        "priority": 80
    },
    {
        "name": "Indian Express India",
        "url": "https://indianexpress.com/section/india/feed/",
        "website": "https://indianexpress.com",
        "category": "India News",
        "active": True,
        "priority": 80
    },
    {
        "name": "Indian Express World",
        "url": "https://indianexpress.com/section/world/feed/",
        "website": "https://indianexpress.com",
        "category": "World News",
        "active": True,
        "priority": 80
    },
    {
        "name": "Hindustan Times",
        "url": "https://www.hindustantimes.com/feeds/rss/india-news/rssfeed.xml",
        "website": "https://www.hindustantimes.com",
        "category": "India News",
        "active": True,
        "priority": 80
    },
    {
        "name": "Hindustan Times World",
        "url": "https://www.hindustantimes.com/feeds/rss/world-news/rssfeed.xml",
        "website": "https://www.hindustantimes.com",
        "category": "World News",
        "active": True,
        "priority": 80
    },
    {
        "name": "Economic Times",
        "url": "https://economictimes.indiatimes.com/rssfeedstopstories.cms",
        "website": "https://economictimes.indiatimes.com",
        "category": "Business & Finance",
        "active": True,
        "priority": 80
    },
    {
        "name": "Economic Times Markets",
        "url": "https://economictimes.indiatimes.com/markets/rssfeeds/1977021501.cms",
        "website": "https://economictimes.indiatimes.com",
        "category": "Business & Finance",
        "active": True,
        "priority": 80
    },
    {
        "name": "Business Standard",
        "url": "https://www.business-standard.com/rss/latest.rss",
        "website": "https://www.business-standard.com",
        "category": "Business & Finance",
        "active": True,
        "priority": 80
    },
    {
        "name": "Moneycontrol",
        "url": "https://www.moneycontrol.com/rss/latestnews.xml",
        "website": "https://www.moneycontrol.com",
        "category": "Business & Finance",
        "active": True,
        "priority": 80
    },
    {
        "name": "Swarajya",
        "url": "https://swarajyamag.com/feed",
        "website": "https://swarajyamag.com",
        "category": "India News",
        "active": True,
        "priority": 80
    },
    {
        "name": "India Today",
        "url": "https://www.indiatoday.in/rss/home",
        "website": "https://www.indiatoday.in",
        "category": "India News",
        "active": True,
        "priority": 80
    },
    {
        "name": "CNBC Top News",
        "url": "https://www.cnbc.com/id/100003114/device/rss/rss.html",
        "website": "https://www.cnbc.com",
        "category": "Business & Finance",
        "active": True,
        "priority": 80
    },
    {
        "name": "CNBC World Markets",
        "url": "https://www.cnbc.com/id/19832390/device/rss/rss.html",
        "website": "https://www.cnbc.com",
        "category": "Business & Finance",
        "active": True,
        "priority": 80
    },
    {
        "name": "CNBC Technology",
        "url": "https://www.cnbc.com/id/19854910/device/rss/rss.html",
        "website": "https://www.cnbc.com",
        "category": "Business & Finance",
        "active": True,
        "priority": 80
    },
    {
        "name": "CNBC Finance",
        "url": "https://www.cnbc.com/id/10000664/device/rss/rss.html",
        "website": "https://www.cnbc.com",
        "category": "Business & Finance",
        "active": True,
        "priority": 80
    },
    {
        "name": "Bloomberg Technology",
        "url": "https://feeds.bloomberg.com/technology/news.rss",
        "website": "https://feeds.bloomberg.com",
        "category": "Technology",
        "active": True,
        "priority": 80
    },
    {
        "name": "Bloomberg Politics",
        "url": "https://feeds.bloomberg.com/politics/news.rss",
        "website": "https://feeds.bloomberg.com",
        "category": "Politics",
        "active": True,
        "priority": 80
    },
    {
        "name": "Bloomberg Markets",
        "url": "https://feeds.bloomberg.com/markets/news.rss",
        "website": "https://feeds.bloomberg.com",
        "category": "Business & Finance",
        "active": True,
        "priority": 80
    },
    {
        "name": "Financial Times World",
        "url": "https://www.ft.com/world?format=rss",
        "website": "https://www.ft.com",
        "category": "Business & Finance",
        "active": True,
        "priority": 80
    },
    {
        "name": "Financial Times Technology",
        "url": "https://www.ft.com/technology?format=rss",
        "website": "https://www.ft.com",
        "category": "Technology",
        "active": True,
        "priority": 80
    },
    {
        "name": "MarketWatch",
        "url": "https://feeds.marketwatch.com/marketwatch/topstories/",
        "website": "https://feeds.marketwatch.com",
        "category": "Business & Finance",
        "active": True,
        "priority": 80
    },
    {
        "name": "MarketWatch Markets",
        "url": "https://feeds.marketwatch.com/marketwatch/marketpulse/",
        "website": "https://feeds.marketwatch.com",
        "category": "Business & Finance",
        "active": True,
        "priority": 80
    },
    {
        "name": "Investing.com News",
        "url": "https://www.investing.com/rss/news.rss",
        "website": "https://www.investing.com",
        "category": "Business & Finance",
        "active": True,
        "priority": 80
    },
    {
        "name": "Fortune",
        "url": "https://fortune.com/feed/",
        "website": "https://fortune.com",
        "category": "Business & Finance",
        "active": True,
        "priority": 80
    },
    {
        "name": "Entrepreneur",
        "url": "https://www.entrepreneur.com/latest.rss",
        "website": "https://www.entrepreneur.com",
        "category": "Business & Finance",
        "active": True,
        "priority": 80
    },
    {
        "name": "Inc.",
        "url": "https://www.inc.com/rss/",
        "website": "https://www.inc.com",
        "category": "Business & Finance",
        "active": True,
        "priority": 80
    },
    {
        "name": "Business Insider",
        "url": "https://feeds.businessinsider.com/custom/all",
        "website": "https://feeds.businessinsider.com",
        "category": "Business & Finance",
        "active": True,
        "priority": 80
    },
    {
        "name": "Quartz",
        "url": "https://qz.com/rss",
        "website": "https://qz.com",
        "category": "Business & Finance",
        "active": True,
        "priority": 80
    },
    {
        "name": "Moneycontrol Markets",
        "url": "https://www.moneycontrol.com/rss/marketreports.xml",
        "website": "https://www.moneycontrol.com",
        "category": "Business & Finance",
        "active": True,
        "priority": 80
    },
    {
        "name": "TechCrunch",
        "url": "https://techcrunch.com/feed/",
        "website": "https://techcrunch.com",
        "category": "Technology",
        "active": True,
        "priority": 80
    },
    {
        "name": "TechCrunch AI",
        "url": "https://techcrunch.com/category/artificial-intelligence/feed/",
        "website": "https://techcrunch.com",
        "category": "AI",
        "active": True,
        "priority": 80
    },
    {
        "name": "The Verge",
        "url": "https://www.theverge.com/rss/index.xml",
        "website": "https://www.theverge.com",
        "category": "Technology",
        "active": True,
        "priority": 80
    },
    {
        "name": "WIRED",
        "url": "https://www.wired.com/feed/rss",
        "website": "https://www.wired.com",
        "category": "Technology",
        "active": True,
        "priority": 80
    },
    {
        "name": "Ars Technica",
        "url": "https://feeds.arstechnica.com/arstechnica/index",
        "website": "https://feeds.arstechnica.com",
        "category": "Technology",
        "active": True,
        "priority": 80
    },
    {
        "name": "Engadget",
        "url": "https://www.engadget.com/rss.xml",
        "website": "https://www.engadget.com",
        "category": "Gadgets & Hardware",
        "active": True,
        "priority": 80
    },
    {
        "name": "CNET News",
        "url": "https://www.cnet.com/rss/news/",
        "website": "https://www.cnet.com",
        "category": "Technology",
        "active": True,
        "priority": 80
    },
    {
        "name": "ZDNET",
        "url": "https://www.zdnet.com/news/rss.xml",
        "website": "https://www.zdnet.com",
        "category": "Technology",
        "active": True,
        "priority": 80
    },
    {
        "name": "VentureBeat",
        "url": "https://venturebeat.com/feed/",
        "website": "https://venturebeat.com",
        "category": "AI",
        "active": True,
        "priority": 80
    },
    {
        "name": "MIT Technology Review",
        "url": "https://www.technologyreview.com/feed/",
        "website": "https://www.technologyreview.com",
        "category": "Technology",
        "active": True,
        "priority": 80
    },
    {
        "name": "IEEE Spectrum",
        "url": "https://spectrum.ieee.org/feeds/feed.rss",
        "website": "https://spectrum.ieee.org",
        "category": "Technology",
        "active": True,
        "priority": 80
    },
    {
        "name": "ScienceDaily Technology",
        "url": "https://www.sciencedaily.com/rss/computers_math/artificial_intelligence.xml",
        "website": "https://www.sciencedaily.com",
        "category": "AI",
        "active": True,
        "priority": 80
    },
    {
        "name": "Google AI Blog",
        "url": "https://blog.google/technology/ai/rss/",
        "website": "https://blog.google",
        "category": "AI",
        "active": True,
        "priority": 80
    },
    {
        "name": "OpenAI News",
        "url": "https://openai.com/news/rss.xml",
        "website": "https://openai.com",
        "category": "AI",
        "active": True,
        "priority": 80
    },
    {
        "name": "Microsoft AI",
        "url": "https://news.microsoft.com/source/topics/ai/feed/",
        "website": "https://news.microsoft.com",
        "category": "AI",
        "active": True,
        "priority": 80
    },
    {
        "name": "NVIDIA Blog",
        "url": "https://blogs.nvidia.com/feed/",
        "website": "https://blogs.nvidia.com",
        "category": "AI",
        "active": True,
        "priority": 80
    },
    {
        "name": "Hugging Face Blog",
        "url": "https://huggingface.co/blog/feed.xml",
        "website": "https://huggingface.co",
        "category": "AI",
        "active": True,
        "priority": 80
    },
    {
        "name": "MarkTechPost",
        "url": "https://www.marktechpost.com/feed/",
        "website": "https://www.marktechpost.com",
        "category": "AI",
        "active": True,
        "priority": 80
    },
    {
        "name": "The Decoder",
        "url": "https://the-decoder.com/feed/",
        "website": "https://the-decoder.com",
        "category": "AI",
        "active": True,
        "priority": 80
    },
    {
        "name": "Towards Data Science",
        "url": "https://towardsdatascience.com/feed",
        "website": "https://towardsdatascience.com",
        "category": "AI",
        "active": True,
        "priority": 80
    },
    {
        "name": "KDnuggets",
        "url": "https://www.kdnuggets.com/feed",
        "website": "https://www.kdnuggets.com",
        "category": "AI",
        "active": True,
        "priority": 80
    },
    {
        "name": "Machine Learning Mastery",
        "url": "https://machinelearningmastery.com/feed/",
        "website": "https://machinelearningmastery.com",
        "category": "AI",
        "active": True,
        "priority": 80
    },
    {
        "name": "Analytics Vidhya",
        "url": "https://www.analyticsvidhya.com/feed/",
        "website": "https://www.analyticsvidhya.com",
        "category": "AI",
        "active": True,
        "priority": 80
    },
    {
        "name": "Hacker News",
        "url": "https://hnrss.org/frontpage",
        "website": "https://hnrss.org",
        "category": "Technology",
        "active": True,
        "priority": 80
    },
    {
        "name": "GitHub Trending",
        "url": "https://mshibanami.github.io/GitHubTrendingRSS/daily/all.xml",
        "website": "https://mshibanami.github.io",
        "category": "Software & Dev",
        "active": True,
        "priority": 80
    },
    {
        "name": "BBC Science",
        "url": "https://feeds.bbci.co.uk/news/science_and_environment/rss.xml",
        "website": "https://feeds.bbci.co.uk",
        "category": "Science & Health",
        "active": True,
        "priority": 80
    },
    {
        "name": "BBC Health",
        "url": "https://feeds.bbci.co.uk/news/health/rss.xml",
        "website": "https://feeds.bbci.co.uk",
        "category": "Science & Health",
        "active": True,
        "priority": 80
    },
    {
        "name": "NPR Health",
        "url": "https://feeds.npr.org/1128/rss.xml",
        "website": "https://feeds.npr.org",
        "category": "Science & Health",
        "active": True,
        "priority": 80
    },
    {
        "name": "NPR Science",
        "url": "https://feeds.npr.org/1007/rss.xml",
        "website": "https://feeds.npr.org",
        "category": "Science & Health",
        "active": True,
        "priority": 80
    },
    {
        "name": "ScienceDaily",
        "url": "https://www.sciencedaily.com/rss/all.xml",
        "website": "https://www.sciencedaily.com",
        "category": "Science & Health",
        "active": True,
        "priority": 80
    },
    {
        "name": "ScienceDaily Health",
        "url": "https://www.sciencedaily.com/rss/health_medicine.xml",
        "website": "https://www.sciencedaily.com",
        "category": "Science & Health",
        "active": True,
        "priority": 80
    },
    {
        "name": "ScienceDaily Environment",
        "url": "https://www.sciencedaily.com/rss/earth_climate.xml",
        "website": "https://www.sciencedaily.com",
        "category": "Energy & Climate",
        "active": True,
        "priority": 80
    },
    {
        "name": "Nature",
        "url": "https://www.nature.com/nature.rss",
        "website": "https://www.nature.com",
        "category": "Science & Health",
        "active": True,
        "priority": 80
    },
    {
        "name": "NASA Breaking News",
        "url": "https://www.nasa.gov/rss/dyn/breaking_news.rss",
        "website": "https://www.nasa.gov",
        "category": "Science & Health",
        "active": True,
        "priority": 80
    },
    {
        "name": "NASA Image of the Day",
        "url": "https://www.nasa.gov/rss/dyn/lg_image_of_the_day.rss",
        "website": "https://www.nasa.gov",
        "category": "Science & Health",
        "active": True,
        "priority": 80
    },
    {
        "name": "Carbon Brief",
        "url": "https://www.carbonbrief.org/feed/",
        "website": "https://www.carbonbrief.org",
        "category": "Energy & Climate",
        "active": True,
        "priority": 80
    },
    {
        "name": "Popular Science",
        "url": "https://popsci.com/feed/",
        "website": "https://popsci.com",
        "category": "Science & Health",
        "active": True,
        "priority": 80
    },
    {
        "name": "STAT News",
        "url": "https://www.statnews.com/feed/",
        "website": "https://www.statnews.com",
        "category": "Science & Health",
        "active": True,
        "priority": 80
    },
    {
        "name": "BBC Sport",
        "url": "https://feeds.bbci.co.uk/sport/rss.xml",
        "website": "https://feeds.bbci.co.uk",
        "category": "Sports",
        "active": True,
        "priority": 80
    },
    {
        "name": "BBC Cricket",
        "url": "https://feeds.bbci.co.uk/sport/cricket/rss.xml",
        "website": "https://feeds.bbci.co.uk",
        "category": "Sports",
        "active": True,
        "priority": 80
    },
    {
        "name": "ESPN Cricket",
        "url": "https://www.espncricinfo.com/rss/content/story/feeds/0.xml",
        "website": "https://www.espncricinfo.com",
        "category": "Sports",
        "active": True,
        "priority": 80
    },
    {
        "name": "Sky Sports",
        "url": "https://www.skysports.com/rss/12040",
        "website": "https://www.skysports.com",
        "category": "Sports",
        "active": True,
        "priority": 80
    },
    {
        "name": "The Guardian Sport",
        "url": "https://www.theguardian.com/uk/sport/rss",
        "website": "https://www.theguardian.com",
        "category": "Sports",
        "active": True,
        "priority": 80
    },
    {
        "name": "Times of India Cricket",
        "url": "https://timesofindia.indiatimes.com/rssfeeds/54829575.cms",
        "website": "https://timesofindia.indiatimes.com",
        "category": "Sports",
        "active": True,
        "priority": 80
    },
    {
        "name": "Formula 1",
        "url": "https://www.formula1.com/content/fom-website/en/latest/all.xml",
        "website": "https://www.formula1.com",
        "category": "Sports",
        "active": True,
        "priority": 80
    },
    {
        "name": "Motorsport",
        "url": "https://www.motorsport.com/rss/f1/news/",
        "website": "https://www.motorsport.com",
        "category": "Sports",
        "active": True,
        "priority": 80
    },
    {
        "name": "CBS Sports",
        "url": "https://www.cbssports.com/rss/headlines/",
        "website": "https://www.cbssports.com",
        "category": "Sports",
        "active": True,
        "priority": 80
    },
    {
        "name": "Yahoo Sports",
        "url": "https://sports.yahoo.com/rss/",
        "website": "https://sports.yahoo.com",
        "category": "Sports",
        "active": True,
        "priority": 80
    },
    {
        "name": "MLB",
        "url": "https://www.mlb.com/feeds/news/rss.xml",
        "website": "https://www.mlb.com",
        "category": "Sports",
        "active": True,
        "priority": 80
    },
    {
        "name": "Reuters Sports via Google News",
        "url": "https://news.google.com/rss/search?q=site%3Areuters.com%20sports&hl=en-US&gl=US&ceid=US:en",
        "website": "https://news.google.com",
        "category": "Sports",
        "active": True,
        "priority": 80
    },
    {
        "name": "Google News Cricket",
        "url": "https://news.google.com/rss/search?q=cricket&hl=en-IN&gl=IN&ceid=IN:en",
        "website": "https://news.google.com",
        "category": "Sports",
        "active": True,
        "priority": 80
    },
    {
        "name": "Al Jazeera Africa",
        "url": "https://www.aljazeera.com/xml/rss/africa.xml",
        "website": "https://www.aljazeera.com",
        "category": "World News",
        "active": False,
        "priority": 60
    },
    {
        "name": "Al Jazeera Asia",
        "url": "https://www.aljazeera.com/xml/rss/asia.xml",
        "website": "https://www.aljazeera.com",
        "category": "World News",
        "active": False,
        "priority": 60
    },
    {
        "name": "France 24 International",
        "url": "https://www.france24.com/en/international/rss",
        "website": "https://www.france24.com",
        "category": "World News",
        "active": False,
        "priority": 60
    },
    {
        "name": "USA Today Top Stories",
        "url": "https://rssfeeds.usatoday.com/usatoday-newstopstories",
        "website": "https://rssfeeds.usatoday.com",
        "category": "World News",
        "active": False,
        "priority": 60
    },
    {
        "name": "Newsweek",
        "url": "https://www.newsweek.com/rss",
        "website": "https://www.newsweek.com",
        "category": "World News",
        "active": False,
        "priority": 60
    },
    {
        "name": "Associated Press Top News",
        "url": "https://feeds.apnews.com/rss/apf-topnews",
        "website": "https://feeds.apnews.com",
        "category": "World News",
        "active": False,
        "priority": 60
    },
    {
        "name": "AP World News",
        "url": "https://feeds.apnews.com/rss/apf-intlnews",
        "website": "https://feeds.apnews.com",
        "category": "World News",
        "active": False,
        "priority": 60
    },
    {
        "name": "AP U.S. News",
        "url": "https://feeds.apnews.com/rss/apf-usnews",
        "website": "https://feeds.apnews.com",
        "category": "World News",
        "active": False,
        "priority": 60
    },
    {
        "name": "Microsoft Start World",
        "url": "https://rss.msn.com/en-us/",
        "website": "https://rss.msn.com",
        "category": "World News",
        "active": False,
        "priority": 60
    },
    {
        "name": "NewsNow World",
        "url": "https://www.newsnow.co.uk/h/World-News/World",
        "website": "https://www.newsnow.co.uk",
        "category": "World News",
        "active": False,
        "priority": 60
    },
    {
        "name": "Voice of America",
        "url": "https://editorials.voa.gov/rss.aspx",
        "website": "https://editorials.voa.gov",
        "category": "World News",
        "active": False,
        "priority": 60
    },
    {
        "name": "Firstpost",
        "url": "https://www.firstpost.com/commonfeeds/v1/mfp-xml-feeds/top.xml",
        "website": "https://www.firstpost.com",
        "category": "India News",
        "active": False,
        "priority": 60
    },
    {
        "name": "Deccan Herald",
        "url": "https://www.deccanherald.com/rss.xml",
        "website": "https://www.deccanherald.com",
        "category": "India News",
        "active": False,
        "priority": 60
    },
    {
        "name": "The Print",
        "url": "https://theprint.in/feed/",
        "website": "https://theprint.in",
        "category": "India News",
        "active": False,
        "priority": 60
    },
    {
        "name": "Scroll.in",
        "url": "https://scroll.in/feed",
        "website": "https://scroll.in",
        "category": "India News",
        "active": False,
        "priority": 60
    },
    {
        "name": "The Wire",
        "url": "https://thewire.in/feed",
        "website": "https://thewire.in",
        "category": "India News",
        "active": False,
        "priority": 60
    },
    {
        "name": "ANI News",
        "url": "https://www.aninews.in/rss/",
        "website": "https://www.aninews.in",
        "category": "India News",
        "active": False,
        "priority": 60
    },
    {
        "name": "Forbes",
        "url": "https://www.forbes.com/forbes billionaire?output=1",
        "website": "https://www.forbes.com",
        "category": "Business & Finance",
        "active": False,
        "priority": 60
    },
    {
        "name": "The Economist",
        "url": "https://www.economist.com/rss",
        "website": "https://www.economist.com",
        "category": "Business & Finance",
        "active": False,
        "priority": 60
    },
    {
        "name": "Harvard Business Review",
        "url": "https://hbr.org/feed",
        "website": "https://hbr.org",
        "category": "Business & Finance",
        "active": False,
        "priority": 60
    },
    {
        "name": "Meta AI",
        "url": "https://ai.meta.com/blog/rss/",
        "website": "https://ai.meta.com",
        "category": "AI",
        "active": False,
        "priority": 60
    },
    {
        "name": "Scientific American",
        "url": "https://rss.sciam.com/ScientificAmerican-Global",
        "website": "https://rss.sciam.com",
        "category": "Science & Health",
        "active": False,
        "priority": 60
    },
    {
        "name": "NOAA Climate",
        "url": "https://www.noaa.gov/news-release/feed",
        "website": "https://www.noaa.gov",
        "category": "Energy & Climate",
        "active": False,
        "priority": 60
    },
    {
        "name": "WHO News",
        "url": "https://www.who.int/rss-feeds/news-english.xml",
        "website": "https://www.who.int",
        "category": "Science & Health",
        "active": False,
        "priority": 60
    },
    {
        "name": "UN News",
        "url": "https://news.un.org/feed/subscribe/en/news/all/rss.xml",
        "website": "https://news.un.org",
        "category": "World News",
        "active": False,
        "priority": 60
    },
    {
        "name": "Climate Central",
        "url": "https://www.climatecentral.org/feed",
        "website": "https://www.climatecentral.org",
        "category": "Energy & Climate",
        "active": False,
        "priority": 60
    },
    {
        "name": "New Scientist",
        "url": "https://www.newscientist.com/feed/home/",
        "website": "https://www.newscientist.com",
        "category": "Science & Health",
        "active": False,
        "priority": 60
    },
    {
        "name": "ESPN",
        "url": "https://www.espn.com/espn/rss/news",
        "website": "https://www.espn.com",
        "category": "Sports",
        "active": False,
        "priority": 60
    },
    {
        "name": "Cricbuzz",
        "url": "https://www.cricbuzz.com/rss-feed",
        "website": "https://www.cricbuzz.com",
        "category": "Sports",
        "active": False,
        "priority": 60
    },
    {
        "name": "Olympics",
        "url": "https://olympics.com/en/news/rss",
        "website": "https://olympics.com",
        "category": "Sports",
        "active": False,
        "priority": 60
    },
    {
        "name": "NBA",
        "url": "https://www.nba.com/rss",
        "website": "https://www.nba.com",
        "category": "Sports",
        "active": False,
        "priority": 60
    },
    {
        "name": "NFL",
        "url": "https://www.nfl.com/rss/rsslanding",
        "website": "https://www.nfl.com",
        "category": "Sports",
        "active": False,
        "priority": 60
    }
]

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
