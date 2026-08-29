"""Async HTTP client with retry logic and rate limiting."""
import asyncio
import logging
import random
from typing import Optional

import httpx

logger = logging.getLogger(__name__)


class ScraperHTTPClient:
    """Async HTTP client with exponential backoff retry and rate limiting."""

    def __init__(
        self,
        max_retries: int = 3,
        base_delay: float = 1.0,
        max_delay: float = 30.0,
        timeout: float = 30.0,
        rate_limit_per_second: float = 10.0,
        user_agent: str = "Mozilla/5.0 (job-scraper personal use)",
    ):
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.timeout = timeout
        self.rate_limit_per_second = rate_limit_per_second
        self._last_request_time = 0.0
        self._rate_limit_lock = asyncio.Lock()
        self._client: Optional[httpx.AsyncClient] = None
        self.default_headers = {"User-Agent": user_agent}

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                timeout=httpx.Timeout(self.timeout),
                headers=self.default_headers,
                limits=httpx.Limits(max_keepalive_connections=20, max_connections=50),
            )
        return self._client

    async def _rate_limit(self):
        """Enforce rate limit between requests."""
        async with self._rate_limit_lock:
            now = asyncio.get_event_loop().time()
            min_interval = 1.0 / self.rate_limit_per_second
            elapsed = now - self._last_request_time
            if elapsed < min_interval:
                await asyncio.sleep(min_interval - elapsed)
            self._last_request_time = asyncio.get_event_loop().time()

    def _calculate_delay(self, attempt: int, response: Optional[httpx.Response] = None) -> float:
        """Calculate delay with exponential backoff and jitter."""
        if response is not None and response.status_code == 429:
            retry_after = response.headers.get("Retry-After")
            if retry_after:
                try:
                    return min(float(retry_after), self.max_delay)
                except ValueError:
                    pass
        delay = min(self.base_delay * (2**attempt), self.max_delay)
        return delay + random.uniform(0, 0.5)

    async def get(
        self,
        url: str,
        params: Optional[dict] = None,
        headers: Optional[dict] = None,
    ) -> httpx.Response:
        """GET request with retry logic."""
        await self._rate_limit()
        client = await self._get_client()
        request_headers = {**self.default_headers, **(headers or {})}

        last_exception = None
        for attempt in range(self.max_retries + 1):
            try:
                response = await client.get(url, params=params, headers=request_headers)
                if response.status_code < 500 and response.status_code != 429:
                    return response
                logger.warning(
                    "Request failed",
                    extra={"url": url, "status": response.status_code, "attempt": attempt + 1},
                )
            except (httpx.TimeoutException, httpx.NetworkError) as e:
                last_exception = e
                logger.warning(
                    "Request error",
                    extra={"url": url, "error": str(e), "attempt": attempt + 1},
                )

            if attempt < self.max_retries:
                delay = self._calculate_delay(attempt, response if "response" in locals() else None)
                logger.info("Retrying", extra={"url": url, "delay": delay, "attempt": attempt + 2})
                await asyncio.sleep(delay)

        if last_exception:
            raise last_exception
        return response

    async def close(self):
        if self._client and not self._client.is_closed:
            await self._client.aclose()

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()


_default_client: Optional[ScraperHTTPClient] = None


async def get_http_client() -> ScraperHTTPClient:
    """Get or create the default HTTP client."""
    global _default_client
    if _default_client is None:
        _default_client = ScraperHTTPClient()
    return _default_client


async def close_http_client():
    """Close the default HTTP client."""
    global _default_client
    if _default_client:
        await _default_client.close()
        _default_client = None