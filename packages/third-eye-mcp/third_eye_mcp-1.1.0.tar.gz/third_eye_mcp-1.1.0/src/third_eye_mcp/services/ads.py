"""Ad content provider for Third Eye MCP with remote fetching."""

import json
import random
import time
import urllib.request
from typing import List, Optional

ADS_URL = "https://grandnasser.com/api/third-eye/ads.json"
CACHE_TTL = 3600  # 1 hour in seconds
REQUEST_TIMEOUT = 2  # seconds

# Cache storage
_cache: dict = {"ads": None, "fetched_at": 0}

# Fallback ads if remote fetch fails
FALLBACK_ADS = [
    "Love Third Eye? Get the ad-free TypeScript version: grandnasser.com/third-eye",
    "Remove ads + support development: $10 at grandnasser.com/third-eye",
    "Third Eye Pro: No ads, faster captures - grandnasser.com/third-eye",
    "Enjoying free captures? Support the project at grandnasser.com/third-eye",
    "Third Eye Premium: Priority support + no ads - grandnasser.com/third-eye",
]


def _fetch_remote_ads() -> Optional[List[str]]:
    """Fetch ads from remote server."""
    try:
        with urllib.request.urlopen(ADS_URL, timeout=REQUEST_TIMEOUT) as response:
            data = json.loads(response.read().decode("utf-8"))
            return data.get("ads", [])
    except Exception:
        return None


def _get_ads() -> List[str]:
    """Get ads with caching."""
    now = time.time()

    # Return cached ads if still valid
    if _cache["ads"] and (now - _cache["fetched_at"]) < CACHE_TTL:
        return _cache["ads"]

    # Try to fetch fresh ads
    remote_ads = _fetch_remote_ads()
    if remote_ads:
        _cache["ads"] = remote_ads
        _cache["fetched_at"] = now
        return remote_ads

    # Return cached ads even if expired (better than nothing)
    if _cache["ads"]:
        return _cache["ads"]

    # Last resort: use fallback
    return FALLBACK_ADS


def get_ad() -> str:
    """Get a random ad message."""
    return random.choice(_get_ads())
