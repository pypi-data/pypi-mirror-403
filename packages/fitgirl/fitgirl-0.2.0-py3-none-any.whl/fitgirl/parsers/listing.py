"""
FitGirl Scraper DOM Parsers - Listing.

Parsers for listing pages and search results.
"""

from __future__ import annotations

from selectolax.parser import HTMLParser

from fitgirl.models import ListingPage, RepackItem, SearchResult
from fitgirl.parsers._utils import (
    _iter_articles,
    _parse_article_preview,
    _parse_pagination,
)

__all__ = ["parse_listing_page", "parse_search_results"]


def parse_listing_page(
    html: bytes,
    *,
    category: str | None = None,
    tag: str | None = None,
) -> ListingPage:
    """
    Parse a listing page (home, category, or tag page).

    Parameters
    ----------
    html
        Raw HTML content as bytes.
    category
        Category filter, if this is a category page.
    tag
        Tag filter, if this is a tag page.

    Returns
    -------
    ListingPage
        Parsed listing with items and pagination.
    """
    tree = HTMLParser(html)
    items: list[RepackItem] = []

    for article in _iter_articles(tree):
        item = _parse_article_preview(article)
        if item:
            items.append(item)

    current_page, total_pages, has_next, has_previous = _parse_pagination(tree)

    return ListingPage(
        items=tuple(items),
        current_page=current_page,
        total_pages=total_pages,
        has_next=has_next,
        has_previous=has_previous,
        category=category,
        tag=tag,
    )


def parse_search_results(html: bytes, query: str) -> SearchResult:
    """
    Parse search results page.

    Parameters
    ----------
    html
        Raw HTML content as bytes.
    query
        The search query string.

    Returns
    -------
    SearchResult
        Parsed search results with items and pagination.
    """
    tree = HTMLParser(html)
    items: list[RepackItem] = []

    for article in _iter_articles(tree):
        item = _parse_article_preview(article)
        if item:
            items.append(item)

    current_page, total_pages, has_next, has_previous = _parse_pagination(tree)

    return SearchResult(
        query=query,
        items=tuple(items),
        current_page=current_page,
        total_pages=total_pages,
        has_next=has_next,
        has_previous=has_previous,
    )
