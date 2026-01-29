"""
FitGirl Scraper Data Models - Pages.

Page and listing-related models.
"""

from __future__ import annotations

from datetime import datetime

import msgspec

from fitgirl.models.repack import RepackItem

__all__ = [
    "SearchResult",
    "ListingPage",
    "ArchivePage",
    "PopularRepack",
    "UpdateDigestEntry",
    "RSSFeedEntry",
]


class SearchResult(msgspec.Struct, frozen=True, kw_only=True):
    """
    Paginated search results.

    Attributes
    ----------
    query
        The search query string.
    items
        List of matching repack items.
    current_page
        Current page number.
    total_pages
        Total number of pages.
    has_next
        Whether there is a next page.
    has_previous
        Whether there is a previous page.
    """

    query: str
    items: tuple[RepackItem, ...] = ()
    current_page: int = 1
    total_pages: int = 1
    has_next: bool = False
    has_previous: bool = False


class ListingPage(msgspec.Struct, frozen=True, kw_only=True):
    """
    Paginated listing page (home, category, or tag page).

    Attributes
    ----------
    items
        List of repack items on this page.
    current_page
        Current page number.
    total_pages
        Total number of pages.
    has_next
        Whether there is a next page.
    has_previous
        Whether there is a previous page.
    category
        Category filter, if applicable.
    tag
        Tag filter, if applicable.
    """

    items: tuple[RepackItem, ...] = ()
    current_page: int = 1
    total_pages: int = 1
    has_next: bool = False
    has_previous: bool = False
    category: str | None = None
    tag: str | None = None


class PopularRepack(msgspec.Struct, frozen=True, kw_only=True):
    """
    A repack from the popular/trending lists.

    Attributes
    ----------
    rank
        Popularity rank (1-based).
    title
        Repack title.
    slug
        URL slug.
    url
        Full URL to the repack page.
    """

    rank: int
    title: str
    slug: str
    url: str


class UpdateDigestEntry(msgspec.Struct, frozen=True, kw_only=True):
    """
    An entry from an updates digest post.

    Attributes
    ----------
    title
        Title of the updated repack.
    slug
        URL slug.
    url
        Full URL to the repack page.
    update_info
        Description of what was updated.
    """

    title: str
    slug: str
    url: str
    update_info: str | None = None


class ArchivePage(msgspec.Struct, frozen=True, kw_only=True):
    """
    Monthly archive page listing.

    Attributes
    ----------
    year
        Archive year.
    month
        Archive month (1-12).
    items
        List of repack items in this month.
    current_page
        Current page number.
    total_pages
        Total number of pages.
    has_next
        Whether there is a next page.
    has_previous
        Whether there is a previous page.
    """

    year: int
    month: int
    items: tuple[RepackItem, ...] = ()
    current_page: int = 1
    total_pages: int = 1
    has_next: bool = False
    has_previous: bool = False


class RSSFeedEntry(msgspec.Struct, frozen=True, kw_only=True):
    """
    An entry from the RSS feed.

    Attributes
    ----------
    title
        Entry title.
    link
        URL to the full post.
    pub_date
        Publication date.
    description
        Entry description/excerpt.
    guid
        Unique identifier.
    """

    title: str
    link: str
    pub_date: datetime | None = None
    description: str | None = None
    guid: str | None = None
