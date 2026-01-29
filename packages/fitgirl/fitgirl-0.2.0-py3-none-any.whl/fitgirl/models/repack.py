"""
FitGirl Scraper Data Models - Repack.

Core repack-related models.
"""

from __future__ import annotations

from datetime import datetime

import msgspec

from fitgirl.models.torrent import DownloadMirror, TorrentSource

__all__ = ["RepackFeatures", "RepackItem", "Repack"]


class RepackFeatures(msgspec.Struct, frozen=True, kw_only=True):
    """
    Parsed repack installation and compression features.

    Attributes
    ----------
    based_on
        Source ISO/release information.
    game_version
        Game version string.
    dlcs_included
        List of included DLCs.
    is_lossless
        Whether the repack is 100% lossless.
    is_md5_perfect
        Whether files match originals after installation.
    selective_download
        Whether selective download is available.
    compression_info
        Details about compression ratio.
    install_time_min
        Minimum installation time description.
    install_time_max
        Maximum installation time description.
    hdd_space_after_install
        Required HDD space after installation.
    ram_required
        Minimum RAM required for installation.
    notes
        Additional installation notes.
    raw_features
        Raw feature list as extracted.
    """

    based_on: str | None = None
    game_version: str | None = None
    dlcs_included: tuple[str, ...] = ()
    is_lossless: bool = False
    is_md5_perfect: bool = False
    selective_download: bool = False
    compression_info: str | None = None
    install_time_min: str | None = None
    install_time_max: str | None = None
    hdd_space_after_install: str | None = None
    ram_required: str | None = None
    notes: tuple[str, ...] = ()
    raw_features: tuple[str, ...] = ()


class RepackItem(msgspec.Struct, frozen=True, kw_only=True):
    """
    A repack listing item (search result or listing preview).

    Attributes
    ----------
    title
        Full title of the repack.
    slug
        URL slug for the repack page.
    url
        Full URL to the repack page.
    repack_number
        FitGirl repack number (e.g., 2586).
    date
        Publication date.
    excerpt
        Short description/excerpt.
    thumbnail_url
        Thumbnail image URL, if available.
    categories
        List of categories.
    tags
        List of tags.
    is_updated
        Whether this is an update to an existing repack.
    """

    title: str
    slug: str
    url: str
    repack_number: int | None = None
    date: datetime | None = None
    excerpt: str | None = None
    thumbnail_url: str | None = None
    categories: tuple[str, ...] = ()
    tags: tuple[str, ...] = ()
    is_updated: bool = False


class Repack(msgspec.Struct, frozen=True, kw_only=True):
    """
    Full repack details from a repack page.

    Attributes
    ----------
    title
        Full title of the repack.
    slug
        URL slug for the repack page.
    url
        Full URL to the repack page.
    repack_number
        FitGirl repack number.
    is_updated
        Whether this is an update to an existing repack.
    date
        Publication date.
    author
        Post author.
    riotpixels_url
        Link to RiotPixels game page.
    genres
        List of genre tags.
    companies
        Developer/publisher companies.
    languages
        Supported languages string.
    original_size
        Original game size.
    repack_size
        Compressed repack size.
    download_mirrors
        Direct download mirrors.
    torrent_sources
        Torrent site sources with magnet links.
    repack_features
        Parsed repack features.
    screenshots
        Screenshot URLs.
    description
        Game description text.
    game_features
        List of game features.
    dlcs_included
        List of included DLCs.
    categories
        Post categories.
    tags
        Post tags.
    cs_rin_url
        Link to CS.RIN.RU discussion thread.
    """

    title: str
    slug: str
    url: str
    repack_number: int | None = None
    is_updated: bool = False
    date: datetime | None = None
    author: str | None = None
    riotpixels_url: str | None = None
    genres: tuple[str, ...] = ()
    companies: tuple[str, ...] = ()
    languages: str | None = None
    original_size: str | None = None
    repack_size: str | None = None
    download_mirrors: tuple[DownloadMirror, ...] = ()
    torrent_sources: tuple[TorrentSource, ...] = ()
    repack_features: RepackFeatures | None = None
    screenshots: tuple[str, ...] = ()
    description: str | None = None
    game_features: tuple[str, ...] = ()
    dlcs_included: tuple[str, ...] = ()
    categories: tuple[str, ...] = ()
    tags: tuple[str, ...] = ()
    cs_rin_url: str | None = None
    related_repacks: tuple[RepackItem, ...] = ()
    cover_url: str | None = None
