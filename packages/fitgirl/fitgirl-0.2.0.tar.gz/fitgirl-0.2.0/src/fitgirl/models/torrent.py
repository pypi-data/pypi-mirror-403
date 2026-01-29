"""
FitGirl Scraper Data Models - Torrent.

Torrent and download-related models.
"""

from __future__ import annotations

from urllib.parse import parse_qs, unquote, urlparse

import msgspec

__all__ = [
    "MagnetLink",
    "TorrentSource",
    "DownloadPart",
    "DownloadMirror",
    "TorrentHealth",
]


class MagnetLink(msgspec.Struct, frozen=True, kw_only=True):
    """
    Parsed magnet URI with extracted components.

    Attributes
    ----------
    raw_uri
        The original magnet URI string.
    info_hash
        The BitTorrent info hash (BTIH) in uppercase.
    display_name
        Human-readable name from the magnet link, if present.
    trackers
        List of tracker announce URLs.
    """

    raw_uri: str
    info_hash: str
    display_name: str | None = None
    trackers: tuple[str, ...] = ()

    @classmethod
    def from_uri(cls, uri: str) -> MagnetLink:
        """
        Parse a magnet URI into structured components.

        Parameters
        ----------
        uri
            Raw magnet URI string.

        Returns
        -------
        MagnetLink
            Parsed magnet link with extracted fields.

        Raises
        ------
        ValueError
            If the URI is not a valid magnet link or lacks info_hash.
        """
        if not uri.startswith("magnet:?"):
            msg = f"Invalid magnet URI: {uri[:50]}"
            raise ValueError(msg)

        parsed = urlparse(uri)
        params = parse_qs(parsed.query)

        # Extract info hash from xt parameter
        xt_values = params.get("xt", [])
        info_hash: str | None = None
        for xt in xt_values:
            if xt.startswith("urn:btih:"):
                info_hash = xt[9:].upper()
                break

        if not info_hash:
            msg = f"No info_hash found in magnet URI: {uri[:50]}"
            raise ValueError(msg)

        # Extract display name
        dn_values = params.get("dn", [])
        display_name = unquote(dn_values[0]) if dn_values else None

        # Extract trackers
        tr_values = params.get("tr", [])
        trackers = tuple(unquote(tr) for tr in tr_values)

        return cls(
            raw_uri=uri,
            info_hash=info_hash,
            display_name=display_name,
            trackers=trackers,
        )


class TorrentHealth(msgspec.Struct, frozen=True, kw_only=True):
    """
    Health statistics for a torrent.

    Attributes
    ----------
    seeds
        Number of active seeders.
    peers
        Number of active leechers.
    downloaded
        Number of completed downloads (if available).
    last_updated
        Timestamp when health was checked.
    """

    seeds: int = 0
    peers: int = 0
    downloaded: int = 0
    last_updated: float = 0.0


class TorrentSource(msgspec.Struct, frozen=True, kw_only=True):
    """
    A torrent source entry (tracker site with links).

    Attributes
    ----------
    name
        Name of the torrent site (e.g., "1337x", "RuTor").
    page_url
        URL to the torrent page on the tracker site.
    magnet
        Parsed magnet link, if available.
    torrent_file_url
        Direct URL to .torrent file, if available.
    """

    name: str
    page_url: str
    magnet: MagnetLink | None = None
    torrent_file_url: str | None = None
    health: TorrentHealth | None = None


class DownloadPart(msgspec.Struct, frozen=True, kw_only=True):
    """
    A single part of a multi-part download.

    Attributes
    ----------
    part_number
        Part index (1-based).
    url
        Direct download URL for this part.
    """

    part_number: int
    url: str


class DownloadMirror(msgspec.Struct, frozen=True, kw_only=True):
    """
    A direct download mirror/hoster.

    Attributes
    ----------
    name
        Name of the file hoster (e.g., "DataNodes", "FuckingFast").
    description
        Additional description or notes about the host.
    parts
        List of download parts (for multi-part downloads).
    single_url
        Single download URL if not multi-part.
    """

    name: str
    description: str | None = None
    parts: tuple[DownloadPart, ...] = ()
    single_url: str | None = None
