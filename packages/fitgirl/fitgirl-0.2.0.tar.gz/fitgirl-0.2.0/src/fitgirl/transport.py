"""
FitGirl Scraper HTTP Transport Layer.

Provides a fully decoupled async HTTP layer using curl_cffi with:
- Browser impersonation for anti-bot bypass
- Configurable retry with exponential backoff
- Async rate limiting
- Proper timeout and error handling
"""

from __future__ import annotations

import asyncio
import logging
import time
from typing import TYPE_CHECKING

from curl_cffi.requests import AsyncSession, BrowserType

from fitgirl.exceptions import (
    HTTPError,
    NetworkError,
    NotFoundError,
    RateLimitError,
    ServerError,
    TimeoutError,
)

if TYPE_CHECKING:
    from types import TracebackType

    from playwright.async_api import Browser as PlaywrightBrowser
    from playwright.async_api import Playwright

__all__ = ["HTTPTransport", "TransportConfig"]

logger = logging.getLogger(__name__)


class TransportConfig:
    """
    Configuration for HTTP transport behavior.

    Attributes
    ----------
    base_url
        Base URL for all requests.
    max_retries
        Maximum number of retry attempts for failed requests.
    base_delay
        Base delay in seconds for exponential backoff.
    max_delay
        Maximum delay in seconds between retries.
    timeout
        Request timeout in seconds.
    requests_per_second
        Rate limit (requests per second). Set to 0 to disable.
    user_agent
        Custom User-Agent header (overrides browser impersonation).
    impersonate
        Browser to impersonate for TLS fingerprinting.
    """

    __slots__ = (
        "base_url",
        "max_retries",
        "base_delay",
        "max_delay",
        "timeout",
        "requests_per_second",
        "user_agent",
        "impersonate",
        "headless_fallback",
    )

    def __init__(
        self,
        *,
        base_url: str = "https://fitgirl-repacks.site",
        max_retries: int = 3,
        base_delay: float = 1.0,
        max_delay: float = 30.0,
        timeout: float = 30.0,
        requests_per_second: float = 2.0,
        user_agent: str | None = None,
        impersonate: BrowserType = BrowserType.chrome131,
        headless_fallback: bool = False,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.timeout = timeout
        self.requests_per_second = requests_per_second
        self.user_agent = user_agent
        self.impersonate = impersonate
        self.headless_fallback = headless_fallback


class RateLimiter:
    """
    Async token bucket rate limiter.

    Attributes
    ----------
    rate
        Requests per second.
    """

    __slots__ = ("_rate", "_tokens", "_last_update", "_lock")

    def __init__(self, rate: float) -> None:
        self._rate = rate
        self._tokens = rate  # Start with full bucket
        self._last_update = time.monotonic()
        self._lock = asyncio.Lock()

    async def acquire(self) -> None:
        """Wait until a request token is available."""
        if self._rate <= 0:
            return

        async with self._lock:
            now = time.monotonic()
            elapsed = now - self._last_update
            self._tokens = min(self._rate, self._tokens + elapsed * self._rate)
            self._last_update = now

            if self._tokens < 1:
                wait_time = (1 - self._tokens) / self._rate
                await asyncio.sleep(wait_time)
                self._tokens = 0
            else:
                self._tokens -= 1


class HTTPTransport:
    """
    Async HTTP transport using curl_cffi.

    Provides browser impersonation, retry logic, rate limiting,
    and proper error handling.

    Parameters
    ----------
    config
        Transport configuration. Uses defaults if not provided.

    Examples
    --------
    >>> async with HTTPTransport() as transport:
    ...     html = await transport.get("/elden-ring/")
    """

    __slots__ = (
        "_config",
        "_session",
        "_rate_limiter",
        "_closed",
        "_playwright",
        "_browser",
    )

    def __init__(self, config: TransportConfig | None = None) -> None:
        self._config = config or TransportConfig()
        self._session: AsyncSession | None = None
        self._rate_limiter = RateLimiter(self._config.requests_per_second)
        self._closed = False
        self._playwright: Playwright | None = None
        self._browser: PlaywrightBrowser | None = None

    def _create_session(self) -> AsyncSession:
        """Create a new async session with configured settings."""
        headers = {}
        if self._config.user_agent:
            headers["User-Agent"] = self._config.user_agent

        return AsyncSession(
            impersonate=self._config.impersonate,  # type: ignore[arg-type]
            headers=headers if headers else None,
            timeout=self._config.timeout,
        )

    @property
    def session(self) -> AsyncSession:
        """Get or create the async session."""
        if self._session is None:
            self._session = self._create_session()
        return self._session

    async def get(self, path: str) -> bytes:
        """
        Perform a GET request with retry and rate limiting.

        Parameters
        ----------
        path
            URL path (appended to base_url) or full URL.

        Returns
        -------
        bytes
            Response body as bytes.

        Raises
        ------
        NotFoundError
            If the resource returns HTTP 404.
        RateLimitError
            If rate limited (HTTP 429).
        ServerError
            If server returns 5xx error.
        HTTPError
            For other HTTP errors.
        NetworkError
            For connection/timeout errors.
        """
        if path.startswith(("http://", "https://")):
            url = path
        else:
            url = f"{self._config.base_url}/{path.lstrip('/')}"

        last_exception: Exception | None = None

        for attempt in range(self._config.max_retries + 1):
            try:
                await self._rate_limiter.acquire()
                response = await self.session.get(url)

                # Handle error responses
                if response.status_code == 404:
                    raise NotFoundError(f"Resource not found: {url}", url=url)

                if response.status_code == 429:
                    retry_after = response.headers.get("Retry-After")
                    retry_seconds = float(retry_after) if retry_after else None
                    raise RateLimitError(
                        f"Rate limited: {url}",
                        url=url,
                        retry_after=retry_seconds,
                    )

                if response.status_code >= 500:
                    raise ServerError(
                        f"Server error {response.status_code}: {url}",
                        status_code=response.status_code,
                        url=url,
                    )

                if response.status_code >= 400:
                    raise HTTPError(
                        f"HTTP {response.status_code}: {url}",
                        status_code=response.status_code,
                        url=url,
                    )

                return response.content

            except (RateLimitError, ServerError) as e:
                # 429/5xx: check if we should fallback to headless
                if self._config.headless_fallback:
                    try:
                        return await self._get_headless(url)
                    except Exception:
                        # If headless fails, continue with normal retry logic
                        pass

                last_exception = e

            except (NotFoundError, HTTPError) as e:
                # HTTP 403: check if we should fallback to headless (Cloudflare)
                if e.status_code == 403 and self._config.headless_fallback:
                    try:
                        return await self._get_headless(url)
                    except Exception:
                        pass

                # Don't retry client errors (except rate limits)
                if not isinstance(e, (RateLimitError, ServerError)):
                    raise
                last_exception = e

            except asyncio.TimeoutError as e:
                last_exception = TimeoutError(
                    f"Request timed out: {url}",
                    url=url,
                    cause=e,
                )

            except Exception as e:
                last_exception = NetworkError(
                    f"Network error: {e}",
                    url=url,
                    cause=e,
                )

            # Calculate backoff delay
            if attempt < self._config.max_retries:
                delay = min(
                    self._config.base_delay * (2**attempt),
                    self._config.max_delay,
                )

                # Use Retry-After if available for rate limits
                if isinstance(last_exception, RateLimitError):
                    if last_exception.retry_after:
                        delay = last_exception.retry_after

                await asyncio.sleep(delay)

        # All retries exhausted
        if last_exception:
            raise last_exception

        # Should never reach here
        raise NetworkError(
            f"Request failed after {self._config.max_retries} retries", url=url
        )

    async def get_json(self, path: str) -> tuple[list | dict, dict[str, str | None]]:
        """
        Perform a GET request expecting JSON, with retry and rate limiting.

        Parameters
        ----------
        path
            URL path (appended to base_url) or full URL.

        Returns
        -------
        tuple[list[dict] | dict, dict[str, str]]
            Tuple of (parsed JSON data, response headers dict).
            Headers include pagination info like X-WP-Total, X-WP-TotalPages.

        Raises
        ------
        NotFoundError
            If the resource returns HTTP 404.
        RateLimitError
            If rate limited (HTTP 429).
        ServerError
            If server returns 5xx error.
        HTTPError
            For other HTTP errors.
        NetworkError
            For connection/timeout errors.
        """
        import json

        if path.startswith(("http://", "https://")):
            url = path
        else:
            url = f"{self._config.base_url}/{path.lstrip('/')}"

        last_exception: Exception | None = None

        for attempt in range(self._config.max_retries + 1):
            try:
                await self._rate_limiter.acquire()
                response = await self.session.get(url)

                # Handle error responses
                if response.status_code == 404:
                    raise NotFoundError(f"Resource not found: {url}", url=url)

                if response.status_code == 429:
                    retry_after = response.headers.get("Retry-After")
                    retry_seconds = float(retry_after) if retry_after else None
                    raise RateLimitError(
                        f"Rate limited: {url}",
                        url=url,
                        retry_after=retry_seconds,
                    )

                if response.status_code >= 500:
                    raise ServerError(
                        f"Server error {response.status_code}: {url}",
                        status_code=response.status_code,
                        url=url,
                    )

                if response.status_code >= 400:
                    raise HTTPError(
                        f"HTTP {response.status_code}: {url}",
                        status_code=response.status_code,
                        url=url,
                    )

                # Parse JSON and extract headers
                data = json.loads(response.content)
                headers = dict(response.headers)
                return data, headers

            except (NotFoundError, HTTPError) as e:
                # Don't retry client errors (except rate limits)
                if not isinstance(e, (RateLimitError, ServerError)):
                    raise
                last_exception = e

            except asyncio.TimeoutError as e:
                last_exception = TimeoutError(
                    f"Request timed out: {url}",
                    url=url,
                    cause=e,
                )

            except json.JSONDecodeError as e:
                last_exception = NetworkError(
                    f"Invalid JSON response: {e}",
                    url=url,
                    cause=e,
                )

            except Exception as e:
                last_exception = NetworkError(
                    f"Network error: {e}",
                    url=url,
                    cause=e,
                )

            # Calculate backoff delay
            if attempt < self._config.max_retries:
                delay = min(
                    self._config.base_delay * (2**attempt),
                    self._config.max_delay,
                )

                # Use Retry-After if available for rate limits
                if isinstance(last_exception, RateLimitError):
                    if last_exception.retry_after:
                        delay = last_exception.retry_after

                await asyncio.sleep(delay)

        # All retries exhausted
        if last_exception:
            raise last_exception

        # Should never reach here
        raise NetworkError(
            f"Request failed after {self._config.max_retries} retries", url=url
        )

    async def _get_headless(self, url: str) -> bytes:
        """
        Perform a GET request using a headless browser (Playwright).

        This is used as a fallback when standard HTTP requests fail due to
        anti-bot protection (Cloudflare).
        """
        try:
            from playwright.async_api import async_playwright
        except ImportError:
            logger.warning("Playwright not installed, headless fallback disabled")
            raise

        if not self._playwright:
            self._playwright = await async_playwright().start()

        if not self._browser:
            self._browser = await self._playwright.chromium.launch(headless=True)

        page = await self._browser.new_page(
            user_agent=self._config.user_agent
            or "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )

        try:
            await page.goto(
                url, wait_until="domcontentloaded", timeout=self._config.timeout * 1000
            )

            # Additional wait for Cloudflare challenge if needed
            title = await page.title()
            if "just a moment" in title.lower():
                await page.wait_for_timeout(5000)

            content = await page.content()
            return content.encode("utf-8")
        except Exception as e:
            logger.error(f"Headless request failed: {e}")
            raise NetworkError(f"Headless request failed: {e}", url=url) from e
        finally:
            await page.close()

    async def head(self, path: str) -> bool:
        """
        Perform a HEAD request to check if a resource exists.

        Parameters
        ----------
        path
            URL path or full URL.

        Returns
        -------
        bool
            True if the resource exists (HTTP 200), False otherwise.
        """
        if path.startswith(("http://", "https://")):
            url = path
        else:
            url = f"{self._config.base_url}/{path.lstrip('/')}"

        try:
            await self._rate_limiter.acquire()
            response = await self.session.head(url)
            return response.status_code == 200
        except Exception:
            return False

    async def close(self) -> None:
        """Close the HTTP session and release resources."""
        if self._session is not None and not self._closed:
            await self._session.close()
            self._session = None

        if self._browser:
            await self._browser.close()
            self._browser = None

        if self._playwright:
            await self._playwright.stop()
            self._playwright = None

        self._closed = True

    async def __aenter__(self) -> HTTPTransport:
        """Enter async context manager."""
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        """Exit async context manager and close session."""
        await self.close()
