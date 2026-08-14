"""Shared helpers for fetchers: URL hygiene + date normalization.

Invariant (security): fetchers must NEVER raise exceptions whose text
contains a request URL with query-string API keys. Keep all request
handling inside try/except and log status codes only.
"""
import re
from datetime import datetime, timezone
from urllib.parse import urlparse, parse_qsl, urlencode, urlunparse

# Tracking / campaign params stripped from article URLs
_TRACKING = re.compile(r"^(utm_|fbclid|gclid|ref_|ref|source|cmpid|mc_|igshid|mkt_tok|yclid|srsltid|gbraid|wbraid)$", re.I)


def clean_url(url):
    """Keep only http(s) URLs; strip tracking params. '' otherwise."""
    if not isinstance(url, str):
        return ""
    u = url.strip()
    if not u.lower().startswith(("http://", "https://")):
        return ""
    try:
        parts = urlparse(u)
        q = [(k, v) for k, v in parse_qsl(parts.query) if not _TRACKING.match(k)]
        return urlunparse(parts._replace(query=urlencode(q)))
    except Exception:
        return u


def iso_utc(value):
    """Normalize common date formats to UTC ISO-8601 ending in Z; '' if unparseable."""
    if not isinstance(value, str):
        return ""
    v = value.strip()
    if not v:
        return ""
    v = v[:26]
    try:
        dt = datetime.fromisoformat(v.replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    except Exception:
        try:
            dt = datetime.strptime(v[:19], "%Y-%m-%d %H:%M:%S")
            return dt.replace(tzinfo=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        except Exception:
            return ""


def safe_title(item):
    """Return stripped title if it is a non-empty string, else ''."""
    t = item.get("title")
    return t.strip() if isinstance(t, str) else ""
