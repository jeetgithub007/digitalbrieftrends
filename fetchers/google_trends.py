"""
Google Trends Fetcher (pytrends)
Handles rate limiting, regional data, suggestions.
"""
import time
import logging
from pytrends.request import TrendReq

logger = logging.getLogger("trend-pipeline.google_trends")

class GoogleTrendsFetcher:
    def __init__(self, proxy=None):
        self.proxy = proxy
        self._pt = None

    @property
    def pt(self):
        """Lazy init — only connect when needed."""
        if self._pt is None:
            logger.info("Connecting to Google Trends...")
            kw = dict(hl="en-US", tz=330)
            if self.proxy:
                kw["proxies"] = [self.proxy]
            self._pt = TrendReq(**kw)
        return self._pt

    def fetch_suggestions(self, keywords):
        """Auto-complete suggestions for content ideas."""
        results = {}
        for kw in keywords:
            try:
                sug = self.pt.suggestions(kw)
                results[kw] = [s["title"] for s in sug[:6]]
                time.sleep(2)
            except Exception as e:
                logger.warning(f"suggestions({kw}): {e}")
                results[kw] = []
                time.sleep(5)
        return results

    def fetch_regional(self, keywords, geo="IN"):
        """Regional interest by Indian state for target keywords."""
        results = {}
        for kw in keywords:
            try:
                self.pt.build_payload([kw], timeframe="today 12-m", geo=geo)
                reg = self.pt.interest_by_region(resolution="REGION")
                if not reg.empty:
                    results[kw] = [
                        {"region": idx, "score": int(row[kw])}
                        for idx, row in reg.sort_values(kw, ascending=False).head(5).iterrows()
                    ]
                time.sleep(4)
            except Exception as e:
                logger.warning(f"regional({kw}): {e}")
                results[kw] = []
                time.sleep(6)
        return results

    def fetch_interest(self, keywords, timeframe="today 1-m"):
        """Interest-over-time: trend direction and peaks."""
        results = {}
        batch_size = 5
        for i in range(0, len(keywords), batch_size):
            batch = keywords[i:i + batch_size]
            try:
                self.pt.build_payload(batch, timeframe=timeframe)
                iot = self.pt.interest_over_time()
                if not iot.empty:
                    for kw in batch:
                        if kw in iot.columns:
                            vals = iot[kw].dropna()
                            if len(vals) > 1:
                                results[kw] = {
                                    "avg": round(float(vals.mean()), 1),
                                    "peak": int(vals.max()),
                                    "latest": int(vals.iloc[-1]),
                                    "trend": "UP" if vals.iloc[-1] > vals.iloc[0] else "DOWN",
                                }
                time.sleep(5)
            except Exception as e:
                logger.warning(f"interest batch {i}: {e}")
                time.sleep(8)
        return results
