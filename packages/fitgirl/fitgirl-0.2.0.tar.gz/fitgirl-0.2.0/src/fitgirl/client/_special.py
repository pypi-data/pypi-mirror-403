"""
FitGirl Scraper Client - Special Pages.

Methods for special pages: popular, updates, A-Z lists, etc.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from fitgirl.parsers import (
    parse_az_list,
    parse_donation_info,
    parse_listing_page,
    parse_popular_repacks,
    parse_updates_digest,
)

if TYPE_CHECKING:
    from fitgirl.models import (
        DonationInfo,
        ListingPage,
        PopularRepack,
        RepackItem,
        UpdateDigestEntry,
    )
    from fitgirl.transport import HTTPTransport

__all__ = ["FitGirlSpecialMethodsMixin"]


class FitGirlSpecialMethodsMixin:
    """Mixin providing special page methods."""

    # Type hints for attributes defined in FitGirlClientBase
    _transport: HTTPTransport

    async def get_popular_monthly(self) -> list[PopularRepack]:
        """
        Get the top 50 most popular repacks of the month.

        Returns
        -------
        list[PopularRepack]
            Ranked list of popular repacks.

        Raises
        ------
        NetworkError
            If the request fails.
        ParseError
            If parsing fails.
        """
        html = await self._transport.get("/popular-repacks/")
        return parse_popular_repacks(html)

    async def get_popular_yearly(self) -> list[PopularRepack]:
        """
        Get the top 150 most popular repacks of the year.

        Returns
        -------
        list[PopularRepack]
            Ranked list of popular repacks.

        Raises
        ------
        NetworkError
            If the request fails.
        ParseError
            If parsing fails.
        """
        html = await self._transport.get("/popular-repacks-of-the-year/")
        return parse_popular_repacks(html)

    async def get_popular_weekly(self) -> list[PopularRepack]:
        """
        Get the most popular repacks of the current week.

        This data is extracted from the sidebar widget.

        Returns
        -------
        list[PopularRepack]
            Popular repacks of the week.

        Raises
        ------
        NetworkError
            If the request fails.
        ParseError
            If parsing fails.
        """
        from selectolax.parser import HTMLParser

        html = await self._transport.get("/")
        tree = HTMLParser(html)

        # Find the sidebar widget for popular repacks
        popular: list[PopularRepack] = []

        # Look for the popular repacks section in sidebar
        widget = tree.css_first("aside#wpp-2, .widget_wpp, #popular-posts-widget")
        if widget:
            rank = 1
            for a in widget.css("a"):
                href = a.attributes.get("href")
                title_attr = a.attributes.get("title") or a.text(strip=True)
                if href and "fitgirl-repacks.site" in href and title_attr:
                    from urllib.parse import urlparse

                    slug = urlparse(href).path.strip("/").split("/")[-1]
                    popular.append(
                        PopularRepack(
                            rank=rank,
                            title=title_attr,
                            slug=slug,
                            url=href,
                        )
                    )
                    rank += 1

        return popular

    async def get_all_repacks_az(self) -> list[RepackItem]:
        """
        Get the complete A-Z list of all repacks.

        Note: This may be a large response.

        Returns
        -------
        list[RepackItem]
            All repacks in alphabetical order.

        Raises
        ------
        NetworkError
            If the request fails.
        ParseError
            If parsing fails.
        """
        html = await self._transport.get("/all-my-repacks-a-z/")
        return parse_az_list(html)

    async def get_switch_repacks(self) -> list[RepackItem]:
        """
        Get all Nintendo Switch emulated repacks.

        Returns
        -------
        list[RepackItem]
            All Switch emulated repacks.

        Raises
        ------
        NetworkError
            If the request fails.
        ParseError
            If parsing fails.
        """
        html = await self._transport.get("/all-switch-emulated-repacks-a-z/")
        return parse_az_list(html)

    async def get_ps3_repacks(self) -> list[RepackItem]:
        """
        Get all PlayStation 3 emulated repacks.

        Returns
        -------
        list[RepackItem]
            All PS3 emulated repacks.

        Raises
        ------
        NetworkError
            If the request fails.
        ParseError
            If parsing fails.
        """
        html = await self._transport.get("/all-playstation-3-emulated-repacks-a-z/")
        return parse_az_list(html)

    async def get_pink_paw_awarded(self) -> list[RepackItem]:
        """
        Get games with FitGirl's personal Pink Paw award.

        These are games personally recommended by FitGirl.

        Returns
        -------
        list[RepackItem]
            Pink Paw awarded games.

        Raises
        ------
        NetworkError
            If the request fails.
        ParseError
            If parsing fails.
        """
        html = await self._transport.get("/games-with-my-personal-pink-paw-award/")
        return parse_az_list(html)

    async def get_updates_list(self) -> list[RepackItem]:
        """
        Get the updates list page showing recently updated repacks.

        Returns
        -------
        list[RepackItem]
            Recently updated repacks.

        Raises
        ------
        NetworkError
            If the request fails.
        ParseError
            If parsing fails.
        """
        html = await self._transport.get("/updates-list/")
        return parse_az_list(html)

    async def get_updates_digest(self, date_slug: str) -> list[UpdateDigestEntry]:
        """
        Get a specific updates digest by date.

        Parameters
        ----------
        date_slug
            Date slug (e.g., "updates-digest-for-january-22-2026").

        Returns
        -------
        list[UpdateDigestEntry]
            Update entries for that date.

        Raises
        ------
        NotFoundError
            If the digest doesn't exist.
        NetworkError
            If the request fails.
        ParseError
            If parsing fails.
        """
        date_slug = date_slug.strip("/")
        html = await self._transport.get(f"/{date_slug}/")
        return parse_updates_digest(html)

    async def get_updates_digest_list(self, page: int = 1) -> ListingPage:
        """
        Get a paginated list of all update digests.

        This returns the category listing at /category/updates-digest/
        which contains links to individual daily update digests.

        Parameters
        ----------
        page
            Page number (1-indexed).

        Returns
        -------
        ListingPage
            Paginated listing of update digest posts.

        Raises
        ------
        NetworkError
            If the request fails.
        ParseError
            If parsing fails.
        """
        path = (
            f"/category/updates-digest/page/{page}/"
            if page > 1
            else "/category/updates-digest/"
        )
        html = await self._transport.get(path)
        return parse_listing_page(html, category="updates-digest")

    async def get_upcoming_repacks(self) -> list[str]:
        """
        Get the list of upcoming repacks.

        Returns
        -------
        list[str]
            Names of upcoming repacks.

        Raises
        ------
        NetworkError
            If the request fails.
        ParseError
            If parsing fails.
        """
        from selectolax.parser import HTMLParser

        html = await self._transport.get("/upcoming-repacks-10/")
        tree = HTMLParser(html)

        content = tree.css_first("div.entry-content")
        if content is None:
            return []

        upcoming: list[str] = []
        for elem in content.css("li, p"):
            text = elem.text(strip=True)
            if text and "⇢" in text:
                # Clean up the text
                name = text.replace("⇢", "").strip()
                if name:
                    upcoming.append(name)

        return upcoming

    async def get_donations_info(self) -> DonationInfo:
        """
        Get donation information and addresses.

        Returns
        -------
        DonationInfo
            Donation addresses and info.

        Raises
        ------
        NetworkError
            If the request fails.
        ParseError
            If parsing fails.
        """
        html = await self._transport.get("/donations/")
        return parse_donation_info(html)
