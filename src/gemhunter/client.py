"""Thin, polite client for the TrustMRR public API.

Docs: https://trustmrr.com/docs/api
- Base URL: https://trustmrr.com/api/v1
- Auth: ``Authorization: Bearer tmrr_...``
- Rate limit: 20 requests / minute / key -> we self-throttle to be safe.
"""

from __future__ import annotations

import os
import time
from typing import Iterator, Optional

import requests
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from .models import Startup

BASE_URL = "https://trustmrr.com/api/v1"

# Sort options accepted by the list endpoint.
VALID_SORTS = {
    "revenue-desc", "revenue-asc",
    "price-desc", "price-asc",
    "multiple-asc", "multiple-desc",
    "growth-desc", "growth-asc",
    "listed-desc", "listed-asc",
    "best-deal",
}


class TrustMRRError(RuntimeError):
    """Raised for non-retryable API problems (auth, bad request, etc.)."""


class TrustMRRClient:
    """Minimal client for listing and fetching startups.

    The API key is never logged. It is read from the ``api_key`` argument or
    the ``TRUSTMRR_API_KEY`` environment variable — do not hard-code it.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        *,
        base_url: str = BASE_URL,
        min_interval: float = 3.2,
        session: Optional[requests.Session] = None,
        timeout: float = 30.0,
    ):
        self.api_key = api_key or os.environ.get("TRUSTMRR_API_KEY")
        if not self.api_key:
            raise TrustMRRError(
                "No API key. Pass api_key=... or set TRUSTMRR_API_KEY in the "
                "environment (keys start with 'tmrr_')."
            )
        if not self.api_key.startswith("tmrr_"):
            raise TrustMRRError("API key looks malformed (should start with 'tmrr_').")

        self.base_url = base_url.rstrip("/")
        self.min_interval = min_interval  # seconds between requests (~18 req/min)
        self.timeout = timeout
        self._last_request = 0.0
        self.session = session or requests.Session()
        self.session.headers.update(
            {
                "Authorization": f"Bearer {self.api_key}",
                "Accept": "application/json",
                "User-Agent": "gemhunter/0.1 (+https://trustmrr.com/docs/api)",
            }
        )

    # ---- low level -------------------------------------------------------

    def _throttle(self) -> None:
        elapsed = time.monotonic() - self._last_request
        if elapsed < self.min_interval:
            time.sleep(self.min_interval - elapsed)

    @retry(
        retry=retry_if_exception_type((requests.RequestException,)),
        wait=wait_exponential(multiplier=2, min=2, max=30),
        stop=stop_after_attempt(4),
        reraise=True,
    )
    def _get(self, path: str, params: Optional[dict] = None) -> dict:
        self._throttle()
        url = f"{self.base_url}/{path.lstrip('/')}"
        resp = self.session.get(url, params=params, timeout=self.timeout)
        self._last_request = time.monotonic()

        if resp.status_code == 429:
            # Rate limited: honour Retry-After then let tenacity retry.
            wait = float(resp.headers.get("Retry-After", "10"))
            time.sleep(min(wait, 60))
            resp.raise_for_status()
        if resp.status_code in (401, 403):
            raise TrustMRRError(f"Authentication failed ({resp.status_code}). Check your API key.")
        if resp.status_code == 404:
            raise TrustMRRError(f"Not found: {url}")
        resp.raise_for_status()
        return resp.json()

    # ---- public API ------------------------------------------------------

    def list_startups(
        self,
        *,
        page: int = 1,
        limit: int = 50,
        sort: str = "revenue-desc",
        category: Optional[str] = None,
        on_sale: Optional[bool] = None,
        extra_params: Optional[dict] = None,
    ) -> tuple[list[Startup], dict]:
        """Return one page of startups plus the pagination ``meta`` block."""
        if sort not in VALID_SORTS:
            raise TrustMRRError(f"Invalid sort '{sort}'. One of: {sorted(VALID_SORTS)}")
        params: dict = {"page": page, "limit": max(1, min(limit, 50)), "sort": sort}
        if category:
            params["category"] = category
        if on_sale is not None:
            params["onSale"] = "true" if on_sale else "false"
        if extra_params:
            params.update(extra_params)

        payload = self._get("startups", params)
        data = payload.get("data", []) or []
        meta = payload.get("meta", {}) or {}
        startups = [Startup.model_validate(item) for item in data]
        return startups, meta

    def iter_startups(
        self,
        *,
        sort: str = "revenue-desc",
        category: Optional[str] = None,
        on_sale: Optional[bool] = None,
        max_pages: int = 6,
        limit: int = 50,
        progress=None,
    ) -> Iterator[Startup]:
        """Yield startups across up to ``max_pages`` pages (respecting rate limits)."""
        page = 1
        while page <= max_pages:
            startups, meta = self.list_startups(
                page=page, limit=limit, sort=sort, category=category, on_sale=on_sale
            )
            for s in startups:
                yield s
            if progress is not None:
                progress(page, meta)
            if not meta.get("hasMore") or not startups:
                break
            page += 1

    def get_startup(self, slug: str) -> Startup:
        payload = self._get(f"startups/{slug}")
        return Startup.model_validate(payload.get("data", payload))
