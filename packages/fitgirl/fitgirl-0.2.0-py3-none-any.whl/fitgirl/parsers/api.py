"""
FitGirl Scraper DOM Parsers - API.

Parsers for WordPress REST API responses.
"""

from __future__ import annotations

from datetime import datetime

from selectolax.parser import HTMLParser

from fitgirl.exceptions import ParseError
from fitgirl.models import APIPostResponse, ListingPage, Repack, RepackItem
from fitgirl.parsers._utils import _parse_repack_number, _safe_text
from fitgirl.parsers.repack import (
    _extract_companies,
    _extract_cs_rin_url,
    _extract_download_mirrors,
    _extract_genres,
    _extract_languages,
    _extract_repack_features,
    _extract_riotpixels_url,
    _extract_screenshots,
    _extract_size,
    _extract_torrent_sources,
)

__all__ = ["parse_repack_from_api_post", "parse_listing_from_api_posts"]


def parse_repack_from_api_post(post: APIPostResponse) -> Repack:
    """
    Parse a repack from a WordPress REST API post response.

    Uses the API for metadata and parses content.rendered HTML for
    download links and features.

    Parameters
    ----------
    post
        APIPostResponse from /wp-json/wp/v2/posts.

    Returns
    -------
    Repack
        Fully parsed repack with all available data.
    """
    # Parse the HTML content from the API response
    content_html = post.content.rendered
    tree = HTMLParser(content_html)
    content = tree.css_first("body") or tree.root

    if content is None:
        raise ParseError("No content in API response", url=post.link)

    # Extract repack number from title or content
    title_text = post.title.rendered
    h3 = tree.css_first("h3")
    h3_text = _safe_text(h3) if h3 else title_text
    repack_number, is_updated = _parse_repack_number(h3_text)

    # Parse date
    date: datetime | None = None
    try:
        date = datetime.fromisoformat(post.date.replace("Z", "+00:00"))
    except ValueError:
        pass

    # Extract all fields using existing extraction functions
    genres = _extract_genres(content)
    companies = _extract_companies(content)
    languages = _extract_languages(content)
    original_size = _extract_size(content, "Original Size")
    repack_size = _extract_size(content, "Repack Size")
    download_mirrors = _extract_download_mirrors(content)
    torrent_sources = _extract_torrent_sources(content)
    repack_features = _extract_repack_features(content)
    screenshots = _extract_screenshots(content)
    riotpixels_url = _extract_riotpixels_url(content)
    cs_rin_url = _extract_cs_rin_url(content)

    # Extract description
    description_parts: list[str] = []
    for p in content.css("p"):
        text = _safe_text(p)
        if any(
            x in text.lower()
            for x in [
                "genres/tags",
                "companies",
                "languages",
                "original size",
                "download",
            ]
        ):
            continue
        if text and len(text) > 50:
            description_parts.append(text)
    description = "\n\n".join(description_parts) if description_parts else None

    return Repack(
        title=title_text,
        slug=post.slug,
        url=post.link,
        repack_number=repack_number,
        is_updated=is_updated,
        date=date,
        author=None,  # Not provided by API posts endpoint
        riotpixels_url=riotpixels_url,
        genres=genres,
        companies=companies,
        languages=languages,
        original_size=original_size,
        repack_size=repack_size,
        download_mirrors=download_mirrors,
        torrent_sources=torrent_sources,
        repack_features=repack_features,
        screenshots=screenshots,
        description=description,
        game_features=(),
        dlcs_included=repack_features.dlcs_included if repack_features else (),
        categories=(),  # Would need category ID resolution
        tags=(),  # Would need tag ID resolution
        cs_rin_url=cs_rin_url,
    )


def parse_listing_from_api_posts(
    posts: list[APIPostResponse],
    *,
    current_page: int = 1,
    total_pages: int = 1,
    category: str | None = None,
    tag: str | None = None,
) -> ListingPage:
    """
    Parse a listing page from WordPress REST API post responses.

    Parameters
    ----------
    posts
        List of APIPostResponse objects from /wp-json/wp/v2/posts.
    current_page
        Current page number.
    total_pages
        Total pages (from X-WP-TotalPages header).
    category
        Category filter, if applicable.
    tag
        Tag filter, if applicable.

    Returns
    -------
    ListingPage
        Parsed listing with items and pagination.
    """
    items: list[RepackItem] = []

    for post in posts:
        # Parse date
        date: datetime | None = None
        try:
            date = datetime.fromisoformat(post.date.replace("Z", "+00:00"))
        except ValueError:
            pass

        # Extract excerpt text (strip HTML)
        excerpt_html = post.excerpt.rendered if post.excerpt else ""
        excerpt_tree = HTMLParser(excerpt_html)
        excerpt = _safe_text(excerpt_tree.root) if excerpt_tree.root else None

        # Extract repack number from title
        title_text = post.title.rendered
        repack_number, is_updated = _parse_repack_number(title_text)

        items.append(
            RepackItem(
                title=title_text,
                slug=post.slug,
                url=post.link,
                repack_number=repack_number,
                date=date,
                excerpt=excerpt,
                thumbnail_url=None,  # Not in basic posts endpoint
                categories=(),  # Would need category ID resolution
                tags=(),  # Would need tag ID resolution
                is_updated=is_updated,
            )
        )

    return ListingPage(
        items=tuple(items),
        current_page=current_page,
        total_pages=total_pages,
        has_next=current_page < total_pages,
        has_previous=current_page > 1,
        category=category,
        tag=tag,
    )
