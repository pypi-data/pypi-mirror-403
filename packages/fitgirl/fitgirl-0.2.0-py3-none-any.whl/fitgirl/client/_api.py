"""
FitGirl Scraper Client - API Methods.

WordPress REST API integration methods.
"""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

import msgspec

from fitgirl.models import (
    APIPostResponse,
    Category,
    ListingPage,
    Repack,
    Tag,
)
from fitgirl.parsers import parse_listing_from_api_posts, parse_repack_from_api_post

if TYPE_CHECKING:
    from fitgirl.transport import HTTPTransport

__all__ = ["FitGirlAPIMethodsMixin"]


class FitGirlAPIMethodsMixin:
    """Mixin providing WordPress REST API methods."""

    # Type hints for attributes defined in FitGirlClientBase
    _transport: HTTPTransport
    _base_url: str

    async def _fetch_posts_from_api(
        self,
        *,
        page: int = 1,
        per_page: int = 10,
        search: str | None = None,
        slug: str | None = None,
        categories: list[int] | None = None,
        categories_exclude: list[int] | None = None,
        tags: list[int] | None = None,
        tags_exclude: list[int] | None = None,
        after: str | None = None,
        before: str | None = None,
        orderby: str = "date",
        order: str = "desc",
        sticky: bool | None = None,
    ) -> tuple[list[APIPostResponse], int, int]:
        """
        Fetch posts from the WordPress REST API.

        Parameters
        ----------
        page
            Page number (1-indexed).
        per_page
            Number of items per page (max 100).
        search
            Optional search query.
        slug
            Optional post slug to filter by.
        categories
            List of category IDs to include.
        categories_exclude
            List of category IDs to exclude.
        tags
            List of tag IDs to include.
        tags_exclude
            List of tag IDs to exclude.
        after
            ISO8601 date - only posts after this date.
        before
            ISO8601 date - only posts before this date.
        orderby
            Sort field: date|modified|id|title|slug|relevance.
        order
            Sort order: asc|desc.
        sticky
            If True, only sticky posts. If False, exclude sticky.

        Returns
        -------
        tuple[list[APIPostResponse], int, int]
            Tuple of (list of posts, total pages, total results).
        """
        params = [f"page={page}", f"per_page={per_page}"]

        if search:
            params.append(f"search={search}")
        if slug:
            params.append(f"slug={slug}")
        if categories:
            params.append(f"categories={','.join(map(str, categories))}")
        if categories_exclude:
            params.append(
                f"categories_exclude={','.join(map(str, categories_exclude))}"
            )
        if tags:
            params.append(f"tags={','.join(map(str, tags))}")
        if tags_exclude:
            params.append(f"tags_exclude={','.join(map(str, tags_exclude))}")
        if after:
            params.append(f"after={after}")
        if before:
            params.append(f"before={before}")
        if orderby != "date":
            params.append(f"orderby={orderby}")
        if order != "desc":
            params.append(f"order={order}")
        if sticky is not None:
            params.append(f"sticky={'true' if sticky else 'false'}")

        path = f"/wp-json/wp/v2/posts?{'&'.join(params)}"
        data, headers = await self._transport.get_json(path)

        # Parse posts using msgspec
        if not isinstance(data, list):
            data = [data]

        posts = [msgspec.convert(post, APIPostResponse, strict=False) for post in data]

        # Extract pagination from headers
        total_pages = 1
        total_results = 0
        if "X-WP-TotalPages" in headers:
            try:
                total_pages = int(headers["X-WP-TotalPages"] or "1")
            except ValueError:
                pass
        if "X-WP-Total" in headers:
            try:
                total_results = int(headers["X-WP-Total"] or "0")
            except ValueError:
                pass

        return posts, total_pages, total_results

    async def get_latest_api(self, page: int = 1, per_page: int = 10) -> ListingPage:
        """
        Get the latest repacks using the WordPress REST API.

        This is more reliable than HTML scraping and provides
        structured pagination data.

        Parameters
        ----------
        page
            Page number (1-indexed).
        per_page
            Number of items per page (max 100).

        Returns
        -------
        ListingPage
            Paginated listing of latest repacks.

        Raises
        ------
        NetworkError
            If the request fails.
        ParseError
            If parsing fails.
        """
        posts, total_pages, _ = await self._fetch_posts_from_api(
            page=page, per_page=per_page
        )
        return parse_listing_from_api_posts(
            posts, current_page=page, total_pages=total_pages
        )

    async def search_api(
        self, query: str, page: int = 1, per_page: int = 10
    ) -> ListingPage:
        """
        Search for repacks using the WordPress REST API.

        Parameters
        ----------
        query
            Search query string.
        page
            Page number (1-indexed).
        per_page
            Number of results per page (max 100).

        Returns
        -------
        ListingPage
            Paginated search results.

        Raises
        ------
        NetworkError
            If the request fails.
        ParseError
            If parsing fails.
        """
        posts, total_pages, _ = await self._fetch_posts_from_api(
            page=page, per_page=per_page, search=query
        )
        return parse_listing_from_api_posts(
            posts, current_page=page, total_pages=total_pages
        )

    async def advanced_search(
        self,
        query: str | None = None,
        page: int = 1,
        per_page: int = 10,
        categories: list[int] | None = None,
        tags: list[int] | None = None,
        after: datetime | None = None,
        before: datetime | None = None,
    ) -> ListingPage:
        """
        Advanced search using WordPress API with filters.

        Parameters
        ----------
        query
            Search query string.
        page
            Page number (1-indexed).
        per_page
            Number of results per page.
        categories
            List of category IDs to include.
        tags
            List of tag IDs to include.
        after
            Include posts after this date.
        before
            Include posts before this date.

        Returns
        -------
        ListingPage
            Paginated search results.
        """
        after_str = after.isoformat() if after else None
        before_str = before.isoformat() if before else None

        posts, total_pages, _ = await self._fetch_posts_from_api(
            page=page,
            per_page=per_page,
            search=query,
            categories=categories,
            tags=tags,
            after=after_str,
            before=before_str,
        )
        return parse_listing_from_api_posts(
            posts, current_page=page, total_pages=total_pages
        )

    async def get_repack_api(self, slug: str) -> Repack:
        """
        Get full repack details using the WordPress REST API.

        Parameters
        ----------
        slug
            The URL slug of the repack (e.g., "elden-ring").

        Returns
        -------
        Repack
            Full repack details including download links, features, etc.

        Raises
        ------
        NotFoundError
            If the repack doesn't exist.
        NetworkError
            If the request fails.
        ParseError
            If parsing fails.
        """
        from fitgirl.exceptions import NotFoundError

        posts, _, _ = await self._fetch_posts_from_api(slug=slug)
        if not posts:
            raise NotFoundError(
                f"Repack not found: {slug}", url=f"{self._base_url}/{slug}/"
            )

        return parse_repack_from_api_post(posts[0])

    async def get_categories(self) -> list[Category]:
        """
        Fetch all categories from the WordPress REST API.

        Returns
        -------
        list[Category]
            List of all available categories with IDs and counts.
        """
        path = "/wp-json/wp/v2/categories?per_page=100"
        data, _ = await self._transport.get_json(path)
        return [msgspec.convert(cat, Category, strict=False) for cat in data]

    async def get_tags_api(self, page: int = 1, per_page: int = 100) -> list[Tag]:
        """
        Fetch tags from the WordPress REST API.

        Parameters
        ----------
        page
            Page number (1-indexed).
        per_page
            Number of tags per page (max 100).

        Returns
        -------
        list[Tag]
            List of tags with IDs and counts.
        """
        path = f"/wp-json/wp/v2/tags?page={page}&per_page={per_page}"
        data, _ = await self._transport.get_json(path)
        return [msgspec.convert(tag, Tag, strict=False) for tag in data]

    async def get_posts_by_category_id(
        self, category_id: int, page: int = 1, per_page: int = 10
    ) -> ListingPage:
        """
        Get posts filtered by WordPress category ID via the API.

        Parameters
        ----------
        category_id
            WordPress category ID (e.g., 5 for Lossless Repack).
        page
            Page number (1-indexed).
        per_page
            Number of results per page.

        Returns
        -------
        ListingPage
            Paginated listing of posts.
        """
        posts, total_pages, _ = await self._fetch_posts_from_api(
            page=page, per_page=per_page, categories=[category_id]
        )
        return parse_listing_from_api_posts(
            posts, current_page=page, total_pages=total_pages
        )

    async def get_posts_by_tag_id(
        self, tag_id: int, page: int = 1, per_page: int = 10
    ) -> ListingPage:
        """
        Get posts filtered by WordPress tag ID via the API.

        Parameters
        ----------
        tag_id
            WordPress tag ID.
        page
            Page number (1-indexed).
        per_page
            Number of results per page.

        Returns
        -------
        ListingPage
            Paginated listing of posts.
        """
        posts, total_pages, _ = await self._fetch_posts_from_api(
            page=page, per_page=per_page, tags=[tag_id]
        )
        return parse_listing_from_api_posts(
            posts, current_page=page, total_pages=total_pages
        )

    async def get_posts_by_date_range(
        self,
        after: datetime | None = None,
        before: datetime | None = None,
        page: int = 1,
        per_page: int = 10,
    ) -> ListingPage:
        """
        Get posts within a specific date range via the API.

        Parameters
        ----------
        after
            Get posts published after this date.
        before
            Get posts published before this date.
        page
            Page number.
        per_page
            Results per page.

        Returns
        -------
        ListingPage
            Paginated listing of posts.
        """
        after_str = after.isoformat() if after else None
        before_str = before.isoformat() if before else None
        posts, total_pages, _ = await self._fetch_posts_from_api(
            page=page,
            per_page=per_page,
            after=after_str,
            before=before_str,
        )
        return parse_listing_from_api_posts(
            posts, current_page=page, total_pages=total_pages
        )

    async def get_russian_movies(self, page: int = 1) -> ListingPage:
        """
        Get posts from the 'Russian Movies' category (ID 41).

        Parameters
        ----------
        page
            Page number.

        Returns
        -------
        ListingPage
            Paginated listing of Russian movies.
        """
        return await self.get_posts_by_category_id(41, page=page)

    async def get_amelie_rd(self, page: int = 1) -> ListingPage:
        """
        Get posts from the 'Amelie R&D Department' category (ID 44).

        Parameters
        ----------
        page
            Page number.

        Returns
        -------
        ListingPage
            Paginated listing of Amelie R&D posts.
        """
        return await self.get_posts_by_category_id(44, page=page)
