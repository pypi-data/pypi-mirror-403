"""
FitGirl Scraper Client.

Main client class combining all functionality.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING
from fitgirl.utils.tracker import TrackerClient

if TYPE_CHECKING:
    from fitgirl.models.torrent import MagnetLink, TorrentHealth

from fitgirl.client._api import FitGirlAPIMethodsMixin
from fitgirl.client._base import FitGirlClientBase
from fitgirl.client._browse import FitGirlBrowseMethodsMixin
from fitgirl.client._special import FitGirlSpecialMethodsMixin
from fitgirl.client._urls import FitGirlURLMethodsMixin

__all__ = ["FitGirlClient"]


class FitGirlClient(
    FitGirlClientBase,
    FitGirlAPIMethodsMixin,
    FitGirlBrowseMethodsMixin,
    FitGirlSpecialMethodsMixin,
    FitGirlURLMethodsMixin,
):
    """
    Async client for interacting with fitgirl-repacks.site.

    Provides methods for searching, browsing, and retrieving repack details
    with full async support, rate limiting, and retry logic.

    Parameters
    ----------
    config
        Optional transport configuration for customizing HTTP behavior.

    Examples
    --------
    >>> async with FitGirlClient() as client:
    ...     # Search for games
    ...     results = await client.search("elden ring")
    ...     for item in results.items:
    ...         print(item.title)
    ...
    ...     # Get full repack details
    ...     repack = await client.get_repack("elden-ring")
    ...     print(f"Size: {repack.repack_size}")
    ...     for source in repack.torrent_sources:
    ...         print(f"  {source.name}: {source.magnet.info_hash}")

    Notes
    -----
    Always use this client as an async context manager to ensure proper
    resource cleanup. Alternatively, call `close()` explicitly when done.
    """

    async def download_torrent_file(self, url: str, path: str | Path) -> None:
        """
        Download a torrent file to the specified path.

        Parameters
        ----------
        url
            URL of the torrent file.
        path
            Destination path (string or Path object).

        Raises
        ------
        NetworkError
            If the download fails.
        """
        path = Path(path)
        if not path.suffix:
            path = path.with_suffix(".torrent")

        content = await self._transport.get(url)

        # Ensure directory exists
        path.parent.mkdir(parents=True, exist_ok=True)

        with open(path, "wb") as f:
            f.write(content)

    async def check_site_availability(self) -> bool:
        """
        Check if the FitGirl site is reachable.

        Returns
        -------
        bool
            True if site is reachable, False otherwise.
        """
        try:
            await self._transport.get("/")
            return True
        except Exception:
            return False

    async def check_magnet_health(
        self, magnet: MagnetLink, timeout: float = 3.0
    ) -> TorrentHealth | None:
        """
        Check health statistics (seeds/peers) for a magnet link.

        Uses UDP tracker scraping to get real-time data.

        Parameters
        ----------
        magnet
            The magnet link to check.
        timeout
            Timeout for tracker responses in seconds.

        Returns
        -------
        TorrentHealth | None
            Health statistics or None if no trackers responded.
        """
        client = TrackerClient(timeout=timeout)
        return await client.check_health(magnet)

    async def check_mirror_status(self, url: str) -> bool:
        """
        Check if a download mirror link is alive.

        Performs a HEAD request to check availability.

        Parameters
        ----------
        url
            The URL to check.

        Returns
        -------
        bool
            True if the link is accessible (HTTP 200), False otherwise.
        """
        return await self._transport.head(url)
