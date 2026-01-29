"""
FitGirl Scraper Custom Exceptions.

All exceptions form a hierarchy under FitGirlError for easy catching
and diagnosable failure modes.
"""

from __future__ import annotations

__all__ = [
    "FitGirlError",
    "NetworkError",
    "TimeoutError",
    "RateLimitError",
    "HTTPError",
    "NotFoundError",
    "ServerError",
    "ParseError",
    "ExtractionError",
]


class FitGirlError(Exception):
    """
    Base exception for all FitGirl scraper errors.

    Attributes
    ----------
    message
        Human-readable error description.
    """

    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(message)


class NetworkError(FitGirlError):
    """
    Base exception for network-related failures.

    Attributes
    ----------
    url
        The URL that failed.
    cause
        The underlying exception, if any.
    """

    def __init__(
        self,
        message: str,
        *,
        url: str | None = None,
        cause: Exception | None = None,
    ) -> None:
        self.url = url
        self.cause = cause
        super().__init__(message)


class TimeoutError(NetworkError):
    """Request timed out."""


class RateLimitError(NetworkError):
    """
    Rate limit exceeded (HTTP 429).

    Attributes
    ----------
    retry_after
        Seconds to wait before retrying, if provided by server.
    """

    def __init__(
        self,
        message: str,
        *,
        url: str | None = None,
        retry_after: float | None = None,
    ) -> None:
        self.retry_after = retry_after
        super().__init__(message, url=url)


class HTTPError(NetworkError):
    """
    HTTP error response.

    Attributes
    ----------
    status_code
        HTTP status code.
    """

    def __init__(
        self,
        message: str,
        *,
        status_code: int,
        url: str | None = None,
    ) -> None:
        self.status_code = status_code
        super().__init__(message, url=url)


class NotFoundError(HTTPError):
    """Resource not found (HTTP 404)."""

    def __init__(self, message: str, *, url: str | None = None) -> None:
        super().__init__(message, status_code=404, url=url)


class ServerError(HTTPError):
    """Server error (HTTP 5xx)."""


class ParseError(FitGirlError):
    """
    Base exception for parsing/extraction failures.

    Attributes
    ----------
    url
        The URL being parsed, if applicable.
    selector
        The CSS selector or XPath that failed, if applicable.
    """

    def __init__(
        self,
        message: str,
        *,
        url: str | None = None,
        selector: str | None = None,
    ) -> None:
        self.url = url
        self.selector = selector
        super().__init__(message)


class ExtractionError(ParseError):
    """Failed to extract a specific field from the DOM."""
