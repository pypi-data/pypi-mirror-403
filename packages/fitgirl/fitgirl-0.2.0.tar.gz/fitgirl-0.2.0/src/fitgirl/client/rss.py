"""
FitGirl Scraper Client - RSS.

RSS feed client for monitoring new releases.
"""

from __future__ import annotations

import xml.etree.ElementTree as ET
from datetime import datetime
from email.utils import parsedate_to_datetime
from typing import TYPE_CHECKING

import msgspec

if TYPE_CHECKING:
    from fitgirl.transport import HTTPTransport

__all__ = ["RSSEntry", "FitGirlRSSClient"]


class RSSEntry(msgspec.Struct, frozen=True, kw_only=True):
    """
    An entry in the RSS feed.

    Attributes
    ----------
    title
        Post title (Repack name).
    link
        URL to the repack page.
    pub_date
        Publication date.
    creator
        Post author.
    guid
        Unique identifier (usually URL).
    description
        HTML description of the repack.
    content
        Full HTML content.
    categories
        List of categories/tags.
    """

    title: str
    link: str
    pub_date: datetime
    creator: str | None = None
    guid: str
    description: str | None = None
    content: str | None = None
    categories: tuple[str, ...] = ()


class FitGirlRSSClient:
    """
    Client for interacting with FitGirl RSS feeds.

    This client is separate from the main client as it handles XML parsing
    rather than HTML scraping or JSON API calls.
    """

    def __init__(self, transport: HTTPTransport, base_url: str) -> None:
        self._transport = transport
        self._base_url = base_url

    async def get_feed(self) -> list[RSSEntry]:
        """
        Fetch and parse the main RSS feed.

        Returns
        -------
        list[RSSEntry]
            List of recent entries from the feed.

        Raises
        ------
        NetworkError
            If the request fails.
        ParseError
            If parsing fails.
        """
        xml_content = await self._transport.get("/feed/")
        return self._parse_feed(xml_content)

    def _parse_feed(self, xml_content: str | bytes) -> list[RSSEntry]:
        """Parse RSS XML content."""
        entries: list[RSSEntry] = []
        try:
            root = ET.fromstring(xml_content)
            channel = root.find("channel")
            if channel is None:
                return []

            namespaces = {
                "content": "http://purl.org/rss/1.0/modules/content/",
                "dc": "http://purl.org/dc/elements/1.1/",
                "atom": "http://www.w3.org/2005/Atom",
                "sy": "http://purl.org/rss/1.0/modules/syndication/",
                "slash": "http://purl.org/rss/1.0/modules/slash/",
            }

            for item in channel.findall("item"):
                title_elem = item.find("title")
                title = (
                    title_elem.text
                    if title_elem is not None and title_elem.text
                    else ""
                )

                link_elem = item.find("link")
                link = (
                    link_elem.text if link_elem is not None and link_elem.text else ""
                )

                pub_date_elem = item.find("pubDate")
                pub_date_str = (
                    pub_date_elem.text
                    if pub_date_elem is not None and pub_date_elem.text
                    else ""
                )
                pub_date = (
                    parsedate_to_datetime(pub_date_str)
                    if pub_date_str
                    else datetime.now()
                )

                guid_elem = item.find("guid")
                guid = (
                    guid_elem.text if guid_elem is not None and guid_elem.text else link
                )

                desc_elem = item.find("description")
                description = desc_elem.text if desc_elem is not None else None

                # Namespaced elements
                creator_elem = item.find("dc:creator", namespaces)
                creator = creator_elem.text if creator_elem is not None else None

                content_elem = item.find("content:encoded", namespaces)
                content = content_elem.text if content_elem is not None else None

                categories = []
                for cat in item.findall("category"):
                    if cat.text:
                        categories.append(cat.text)

                entries.append(
                    RSSEntry(
                        title=title,
                        link=link,
                        pub_date=pub_date,
                        creator=creator,
                        guid=guid,
                        description=description,
                        content=content,
                        categories=tuple(categories),
                    )
                )

        except ET.ParseError as e:
            from fitgirl.exceptions import ParseError

            raise ParseError(
                f"Failed to parse RSS feed: {e}", url=f"{self._base_url}/feed/"
            ) from e

        return entries
