"""
FitGirl Scraper Data Models - Taxonomy.

WordPress taxonomy models for categories and tags.
"""

from __future__ import annotations

import msgspec

__all__ = ["Category", "Tag"]


class Category(msgspec.Struct, frozen=True, kw_only=True):
    """
    WordPress category taxonomy.

    Used for API-based category filtering via ID.

    Attributes
    ----------
    id
        WordPress category ID.
    name
        Category display name.
    slug
        URL-friendly slug.
    count
        Number of posts in this category.
    description
        Category description (often empty).
    link
        Full URL to the category page.
    """

    id: int
    name: str
    slug: str
    count: int
    description: str = ""
    link: str = ""


class Tag(msgspec.Struct, frozen=True, kw_only=True):
    """
    WordPress post tag taxonomy.

    Used for API-based tag filtering via ID.

    Attributes
    ----------
    id
        WordPress tag ID.
    name
        Tag display name.
    slug
        URL-friendly slug.
    count
        Number of posts with this tag.
    link
        Full URL to the tag page.
    """

    id: int
    name: str
    slug: str
    count: int
    link: str = ""
