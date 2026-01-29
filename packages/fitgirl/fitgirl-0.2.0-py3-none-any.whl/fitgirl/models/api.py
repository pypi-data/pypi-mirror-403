"""
FitGirl Scraper Data Models - API.

WordPress REST API response models.
"""

from __future__ import annotations

import msgspec

__all__ = ["APIRenderedField", "APIPostResponse"]


class APIRenderedField(msgspec.Struct, frozen=True, kw_only=True):
    """
    A WordPress API field with rendered HTML content.

    Many WP API fields return {"rendered": "<html>"} objects.

    Attributes
    ----------
    rendered
        The rendered HTML content.
    """

    rendered: str = ""


class APIPostResponse(msgspec.Struct, frozen=True, kw_only=True):
    """
    WordPress REST API post response structure.

    Maps to /wp-json/wp/v2/posts endpoint responses.

    Attributes
    ----------
    id
        WordPress post ID.
    date
        Publication date in ISO format.
    slug
        Post URL slug.
    link
        Full permalink URL.
    title
        Post title (rendered HTML).
    content
        Post content (rendered HTML).
    excerpt
        Post excerpt (rendered HTML).
    categories
        List of category IDs.
    tags
        List of tag IDs.
    """

    id: int
    date: str
    slug: str
    link: str
    title: APIRenderedField
    content: APIRenderedField
    excerpt: APIRenderedField | None = None
    categories: tuple[int, ...] = ()
    tags: tuple[int, ...] = ()
