"""
FitGirl Scraper Client - Base.

Core client infrastructure: initialization, lifecycle, and context management.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Self

from fitgirl.transport import HTTPTransport, TransportConfig

if TYPE_CHECKING:
    from types import TracebackType

__all__ = ["FitGirlClientBase"]


class FitGirlClientBase:
    """
    Base client with core infrastructure.

    Provides initialization, transport management, and async context manager.

    Parameters
    ----------
    config
        Optional transport configuration for customizing HTTP behavior.

    Notes
    -----
    Always use this client as an async context manager to ensure proper
    resource cleanup. Alternatively, call `close()` explicitly when done.
    """

    __slots__ = ("_transport", "_base_url")

    def __init__(self, config: TransportConfig | None = None) -> None:
        self._transport = HTTPTransport(config)
        config = config or TransportConfig()
        self._base_url = config.base_url

    async def close(self) -> None:
        """
        Close the client and release resources.

        This is called automatically when using the client as an
        async context manager.
        """
        await self._transport.close()

    async def __aenter__(self) -> Self:
        """Enter async context manager."""
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        """Exit async context manager and close resources."""
        await self.close()
