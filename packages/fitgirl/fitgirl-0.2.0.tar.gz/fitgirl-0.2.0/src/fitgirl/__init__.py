"""
FitGirl Repacks Scraper.

A production-grade, fully asynchronous scraper for fitgirl-repacks.site
with strict typing, robust error handling, and comprehensive data extraction.

Examples
--------
>>> import asyncio
>>> from fitgirl import FitGirlClient
>>>
>>> async def main():
...     async with FitGirlClient() as client:
...         # Search for games
...         results = await client.search("elden ring")
...         print(f"Found {len(results.items)} results")
...
...         # Get repack details
...         repack = await client.get_repack("elden-ring")
...         print(f"Title: {repack.title}")
...         print(f"Size: {repack.repack_size}")
...
...         # Get magnet links
...         for source in repack.torrent_sources:
...             if source.magnet:
...                 print(f"  {source.name}: {source.magnet.info_hash}")
>>>
>>> asyncio.run(main())
"""

from __future__ import annotations

# Client
from fitgirl.client import FitGirlClient

# Exceptions
from fitgirl.exceptions import (
    ExtractionError,
    FitGirlError,
    HTTPError,
    NetworkError,
    NotFoundError,
    ParseError,
    RateLimitError,
    ServerError,
    TimeoutError,
)

# Models
from fitgirl.models import (
    ArchivePage,
    Category,
    DownloadMirror,
    DownloadPart,
    ListingPage,
    MagnetLink,
    PopularRepack,
    Repack,
    RepackFeatures,
    RepackItem,
    RSSFeedEntry,
    SearchResult,
    Tag,
    TorrentSource,
    UpdateDigestEntry,
)

# Transport (for advanced configuration)
from fitgirl.transport import HTTPTransport, TransportConfig

__all__ = [
    # Client
    "FitGirlClient",
    # Models
    "ArchivePage",
    "Category",
    "DownloadMirror",
    "DownloadPart",
    "ListingPage",
    "MagnetLink",
    "PopularRepack",
    "Repack",
    "RepackFeatures",
    "RepackItem",
    "RSSFeedEntry",
    "SearchResult",
    "Tag",
    "TorrentSource",
    "UpdateDigestEntry",
    # Exceptions
    "FitGirlError",
    "NetworkError",
    "TimeoutError",
    "RateLimitError",
    "HTTPError",
    "NotFoundError",
    "ServerError",
    "ParseError",
    "ExtractionError",
    # Transport
    "HTTPTransport",
    "TransportConfig",
]

__version__ = "0.2.0"
