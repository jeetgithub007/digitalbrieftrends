# Trend Pipeline

Multi-source trend aggregation service — fetches trending topics from Google Trends, NewsAPI, Reddit, and RSS feeds, deduplicates, scores, and serves them via a REST API and live dashboard.

Built for **DigitalBrief** and **Jeet Digital Marketing Agency**.

---

## Quick Start

```powershell
cd trend-pipeline
pip install -r requirements.txt
python server.py
```

Then open **http://localhost:8765** for the dashboard.

---

## Architecture

```
┌────────────────────────────────────────────────────────┐
│                    TREND PIPELINE                       │
├──────────┬──────────┬──────────┬───────────────────────┤
│ Google   │ NewsAPI  │  Reddit  │  RSS Feeds            │
│ Trends   │ (80K+    │ (r/tech  │  (TechCrunch,         │
│ (pytrends│  sources)│  r/ai…)  │   Verge, Ars, HN…)   │
├──────────┴──────────┴──────────┴───────────────────────┤
│              Trend Aggregator Engine                    │
│    Merge → Deduplicate → Score → Rank → Cache          │
├────────────────────────────────────────────────────────┤
│              REST API (FastAPI)                         │
│    GET /api/trends  GET /api/trends/top               │
│    GET /api/trends/ideas  GET /api/trends/status      │
├────────────────────────────────────────────────────────┤
│              Dashboard (HTML)                           │
│    Real-time filters, scoring, content ideas           │
└────────────────────────────────────────────────────────┘
```

---

## Project Structure

| File | Purpose |
|------|---------|
| `server.py` | FastAPI server — REST API + dashboard + pipeline orchestration |
| `engine.py` | Pipeline engine — coordinates all fetchers, refresh loop |
| `aggregator.py` | Merges, deduplicates, scores, and ranks trends |
| `cache.py` | Thread-safe in-memory cache |
| `config.py` | All configuration — API keys, keywords, intervals |
| `fetchers/google_trends.py` | pytrends: suggestions, regional, interest data |
| `fetchers/newsapi.py` | NewsAPI: headlines from 80K+ sources |
| `fetchers/reddit.py` | Reddit: hot posts from configured subreddits |
| `fetchers/rss.py` | RSS: entries from major tech/business publications |
| `dashboard.html` | Self-contained dashboard UI |

---

## API Keys Needed

| Service | Required? | Signup Link | Free Tier |
|---------|-----------|-------------|-----------|
| Google Trends | No | None | Always free |
| NewsAPI | Recommended | https://newsapi.org/register | 100 req/day |
| Reddit | Recommended | https://www.reddit.com/prefs/apps | Free (script app) |
| RSS Feeds | No | None | Always free |

**Without NewsAPI/Reddit keys:** The pipeline still runs — those sources are simply skipped. You'll get Google Trends + RSS data.

Set keys via environment variables or edit `config.py`:

```powershell
$env:NEWSAPI_KEY = "your_key"
$env:REDDIT_CLIENT_ID = "your_id"
$env:REDDIT_CLIENT_SECRET = "your_secret"
```

---

## API Endpoints

| Endpoint | Description |
|----------|-------------|
| `GET /` | Dashboard (HTML) |
| `GET /docs` | Swagger API docs |
| `GET /api/trends` | All trends (filterable: `?source=` `&min_score=` `&limit=` `&category=`) |
| `GET /api/trends/top?n=10` | Top N trends |
| `GET /api/trends/ideas?min_score=50` | Content article ideas |
| `GET /api/trends/status` | Pipeline health, refresh info, errors |
| `GET /api/trends/refresh` | Force immediate refresh |

---

## Integration with WordPress / Web App

### 1. WordPress Shortcode (PHP)

```php
function digitalbrief_trending_feed($atts) {
    $atts = shortcode_atts(['count' => 10, 'min_score' => 40], $atts);
    $response = wp_remote_get("http://localhost:8765/api/trends?limit={$atts['count']}&min_score={$atts['min_score']}");
    $body = json_decode(wp_remote_retrieve_body($response), true);
    ob_start(); ?>
    <div class="trending-widget">
        <h4>🔥 Trending</h4>
        <ol><?php foreach ($body['data'] as $t): ?>
            <li><a href="<?= esc_url($t['url'] ?? '#') ?>"><?= esc_html($t['title']) ?></a></li>
        <?php endforeach; ?></ol>
    </div><?php
    return ob_get_clean();
}
add_shortcode('trending_news', 'digitalbrief_trending_feed');
```

### 2. JavaScript Widget (any site)

```html
<fetch-trends count="8"></fetch-trends>
<script>
class FetchTrends extends HTMLElement {
  async connectedCallback() {
    const count = this.getAttribute('count') || 8;
    const res = await fetch(`http://localhost:8765/api/trends/top?n=${count}`);
    const { data } = await res.json();
    this.innerHTML = data.map(t => 
      `<div class="trend-item">#${t.rank} <a href="#">${t.title}</a></div>`
    ).join('');
  }
}
customElements.define('fetch-trends', FetchTrends);
</script>
```

---

## How Scoring Works

Each trend gets a composite `trend_score` (0-100):

| Factor | Weight |
|--------|--------|
| Source authority (Google > Reddit > NewsAPI > RSS) | Base weight |
| Reddit upvotes | +0-30 |
| Reddit comments | +0-20 |
| Google search volume | +0-25 |
| Multi-source appearance | +25 bonus |
| Duplicate detected (>78% title similarity) | Merged + bonus |

---

## Customization

### Add your own keywords

Edit `config.py` → `CONTENT_KEYWORDS` list. These are used for Google Trends lookups.

### Add RSS feeds

Edit `config.py` → `RSS_FEEDS` list. Each entry is `("Display Name", "feed_url")`.

### Change refresh interval

Edit `config.py` → `REFRESH_INTERVAL_MINUTES`. Default: 30 minutes.

### Change port

```powershell
$env:TREND_PORT = "8080"
python server.py
```

---

## Production Deployment

```powershell
# Install as Windows service or use a process manager
pip install uvicorn[standard]

# Run with production settings
uvicorn server:app --host 0.0.0.0 --port 8765 --workers 1

# Or with gunicorn (Linux)
gunicorn server:app -w 1 -k uvicorn.workers.UvicornWorker -b 0.0.0.0:8765
```

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| 429 Rate Limit | Google Trends blocking — try residential IP or proxy in `config.py` → `GOOGLE_TRENDS_PROXY` |
| No Reddit data | Verify `REDDIT_CLIENT_ID` and `REDDIT_CLIENT_SECRET` are set |
| Empty dashboard | Check `http://localhost:8765/api/trends/status` — pipeline may still be fetching |
| ModuleNotFoundError | Run `pip install -r requirements.txt` |
