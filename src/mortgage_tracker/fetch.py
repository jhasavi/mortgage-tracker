import logging
from typing import Optional
import time
import requests

logger = logging.getLogger("mortgage_tracker.fetch")


def fetch_url(url: str, timeout: float = 10.0, retries: int = 2, backoff: float = 1.5, headers: Optional[dict] = None) -> tuple:
    """Fetch a URL with basic retry. Returns (status, text, json)."""
    if not url:
        raise ValueError("rate_url is required for fetching")
    session = requests.Session()
    last_exc: Optional[Exception] = None
    for attempt in range(retries + 1):
        try:
            resp = session.get(url, timeout=timeout, headers=headers)
            status = resp.status_code
            text = None
            js = None
            # Try JSON if content-type indicates
            ct = resp.headers.get("content-type", "")
            if "application/json" in ct:
                try:
                    js = resp.json()
                except Exception as e:
                    logger.warning("json_parse_error", extra={"url": url, "error": str(e)})
                    text = resp.text
            else:
                text = resp.text
            return status, text, js
        except Exception as e:
            last_exc = e
            logger.warning("fetch_error", extra={"url": url, "attempt": attempt, "error": str(e)})
            if attempt < retries:
                time.sleep(backoff ** attempt)
            else:
                break
    # Final failure
    logger.error("fetch_failed", extra={"url": url, "error": str(last_exc) if last_exc else "unknown"})
    return 0, None, None
