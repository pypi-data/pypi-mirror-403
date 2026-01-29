"""
FitGirl Scraper DOM Parsers - Utilities.

Internal helpers, regex patterns, and common extraction functions.
"""

from __future__ import annotations

import re
from datetime import datetime
from typing import TYPE_CHECKING
from urllib.parse import urlparse

from selectolax.parser import HTMLParser, Node

from fitgirl.models import RepackItem

if TYPE_CHECKING:
    from collections.abc import Iterator

__all__ = [
    # Constants
    "BASE_URL",
    "RE_REPACK_NUMBER",
    "RE_SIZE",
    "RE_DATETIME",
    "RE_SLUG",
    # Helpers
    "_safe_text",
    "_safe_attr",
    "_extract_slug",
    "_parse_datetime",
    "_parse_repack_number",
    "_iter_articles",
    "_parse_article_preview",
    "_parse_pagination",
]

# Constants
BASE_URL = "https://fitgirl-repacks.site"

# Regex patterns (compiled for performance)
RE_REPACK_NUMBER = re.compile(r"#(\d+)\s*(?:Updated)?", re.IGNORECASE)
RE_SIZE = re.compile(r"(\d+(?:\.\d+)?)\s*(GB|MB|TB)", re.IGNORECASE)
RE_DATETIME = re.compile(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}")
RE_SLUG = re.compile(r"fitgirl-repacks\.site/([^/]+)/?$")


def _safe_text(node: Node | None, default: str = "") -> str:
    """Safely extract text from a node, returning default if None."""
    if node is None:
        return default
    return node.text(strip=True) or default


def _safe_attr(node: Node | None, attr: str, default: str = "") -> str:
    """Safely extract an attribute from a node."""
    if node is None:
        return default
    return node.attributes.get(attr, default) or default


def _extract_slug(url: str) -> str:
    """Extract the slug from a FitGirl repack URL."""
    match = RE_SLUG.search(url)
    if match:
        return match.group(1)
    # Fallback: get the last path segment
    path = urlparse(url).path.strip("/")
    return path.split("/")[-1] if path else ""


def _parse_datetime(value: str) -> datetime | None:
    """Parse an ISO datetime string."""
    match = RE_DATETIME.search(value)
    if match:
        try:
            return datetime.fromisoformat(match.group(0))
        except ValueError:
            pass
    return None


def _parse_repack_number(text: str) -> tuple[int | None, bool]:
    """
    Extract repack number and updated status from header text.

    Returns
    -------
    tuple
        (repack_number, is_updated)
    """
    match = RE_REPACK_NUMBER.search(text)
    if match:
        number = int(match.group(1))
        is_updated = "updated" in text.lower()
        return number, is_updated
    return None, False


def _iter_articles(tree: HTMLParser) -> Iterator[Node]:
    """Iterate over article elements in the DOM."""
    for article in tree.css("article.post"):
        yield article


def _parse_article_preview(article: Node) -> RepackItem | None:
    """
    Parse an article element into a RepackItem.

    Used for search results and listing pages.
    """
    # Extract title and URL
    title_link = article.css_first("h1.entry-title a, h2.entry-title a")
    if title_link is None:
        return None

    title = _safe_text(title_link)
    url = _safe_attr(title_link, "href")
    if not url:
        return None

    slug = _extract_slug(url)

    # Extract date
    time_elem = article.css_first("time.entry-date")
    date_str = _safe_attr(time_elem, "datetime")
    date = _parse_datetime(date_str) if date_str else None

    # Extract excerpt
    summary_div = article.css_first("div.entry-summary, div.entry-content")
    excerpt = _safe_text(summary_div) if summary_div else None

    # Extract thumbnail
    thumbnail = article.css_first("img.attachment-post-thumbnail, img.wp-post-image")
    thumbnail_url = _safe_attr(thumbnail, "src") if thumbnail else None

    # Extract categories
    cat_links = article.css("span.cat-links a")
    categories = tuple(_safe_text(a) for a in cat_links if _safe_text(a))

    # Extract tags
    tag_links = article.css("span.tags-links a, footer.entry-meta a[rel='tag']")
    tags = tuple(_safe_text(a) for a in tag_links if _safe_text(a))

    # Try to extract repack number from header
    header_elem = article.css_first("h3")
    header_text = _safe_text(header_elem) if header_elem else ""
    repack_number, is_updated = _parse_repack_number(header_text)

    return RepackItem(
        title=title,
        slug=slug,
        url=url,
        repack_number=repack_number,
        date=date,
        excerpt=excerpt,
        thumbnail_url=thumbnail_url,
        categories=categories,
        tags=tags,
        is_updated=is_updated,
    )


def _parse_pagination(tree: HTMLParser) -> tuple[int, int, bool, bool]:
    """
    Parse pagination from the page.

    Returns
    -------
    tuple
        (current_page, total_pages, has_next, has_previous)
    """
    current_page = 1
    total_pages = 1
    has_next = False
    has_previous = False

    # Method 1: Extract from page title (e.g., "Page 2 of 709")
    title = tree.css_first("title")
    if title:
        title_text = title.text() or ""
        page_match = re.search(r"Page\s+(\d+)\s+of\s+(\d+)", title_text, re.IGNORECASE)
        if page_match:
            current_page = int(page_match.group(1))
            total_pages = int(page_match.group(2))

    # Method 2: Try various nav element selectors
    nav_selectors = [
        "nav.navigation.pagination",
        "nav.posts-navigation",
        "div.nav-links",
        ".navigation.posts-navigation",
        "nav.pagination",
    ]

    nav = None
    for selector in nav_selectors:
        nav = tree.css_first(selector)
        if nav:
            break

    if nav:
        # Find all page number links
        page_links = nav.css("a.page-numbers, span.page-numbers, a.page-link")
        page_numbers: list[int] = []

        for link in page_links:
            text = _safe_text(link)
            # Skip "Next" and "Previous" links
            if text.lower() in (
                "next",
                "prev",
                "previous",
                "→",
                "←",
                "older posts",
                "newer posts",
            ):
                continue
            # Check if this is the current page
            if "current" in (_safe_attr(link, "class") or ""):
                try:
                    current_page = int(text)
                except ValueError:
                    pass
            # Extract page number
            try:
                page_numbers.append(int(text))
            except ValueError:
                pass

        if page_numbers:
            total_pages = max(max(page_numbers), total_pages)

        # Check for next/prev links
        has_next = nav.css_first("a.next, a.nav-next, a[rel='next']") is not None
        has_previous = (
            nav.css_first("a.prev, a.nav-previous, a[rel='prev']") is not None
        )
    else:
        # Method 3: Check for older/newer posts links anywhere
        older = tree.css_first("a.nav-previous, .nav-previous a, a[rel='next']")
        newer = tree.css_first("a.nav-next, .nav-next a, a[rel='prev']")
        has_next = older is not None  # "Older posts" is the "next" page
        has_previous = newer is not None  # "Newer posts" is the "previous" page

    # Infer pagination state
    if current_page > 1:
        has_previous = True
    if current_page < total_pages:
        has_next = True

    return current_page, total_pages, has_next, has_previous
