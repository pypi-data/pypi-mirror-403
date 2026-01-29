"""
FitGirl Scraper Data Models.

All domain models are implemented as msgspec.Struct for maximum performance,
strict typing, and zero-copy deserialization where applicable.

This package provides a modular structure with models organized by domain:
- taxonomy: WordPress categories and tags
- torrent: Magnet links, torrent sources, and download mirrors
- repack: Core repack data structures
- pages: Listing pages, search results, and archives
- api: WordPress REST API response models
"""

from __future__ import annotations

# Taxonomy models
from fitgirl.models.taxonomy import Category, Tag

# Donation model
from fitgirl.models.donation import DonationInfo

# Torrent/download models
from fitgirl.models.torrent import (
    DownloadMirror,
    DownloadPart,
    MagnetLink,
    TorrentSource,
)

# Repack models
from fitgirl.models.repack import Repack, RepackFeatures, RepackItem

# Page/listing models
from fitgirl.models.pages import (
    ArchivePage,
    ListingPage,
    PopularRepack,
    RSSFeedEntry,
    SearchResult,
    UpdateDigestEntry,
)

# API response models
from fitgirl.models.api import APIPostResponse, APIRenderedField

__all__ = [
    # Taxonomy
    "Category",
    "Tag",
    # Torrent/download
    "MagnetLink",
    "TorrentSource",
    "DownloadMirror",
    "DownloadPart",
    # Repack
    "RepackFeatures",
    "RepackItem",
    "Repack",
    # Pages
    "SearchResult",
    "ListingPage",
    "PopularRepack",
    "UpdateDigestEntry",
    "ArchivePage",
    "RSSFeedEntry",
    # API
    "APIRenderedField",
    "APIPostResponse",
    "DonationInfo",
]
