"""
FitGirl Scraper Client - URL Methods.

Simple URL getters for static pages.
"""

from __future__ import annotations

__all__ = ["FitGirlURLMethodsMixin"]


class FitGirlURLMethodsMixin:
    """Mixin providing URL getter methods."""

    # Type hints for attributes defined in FitGirlClientBase
    _base_url: str

    def get_rss_feed_url(self) -> str:
        """
        Get the URL of the RSS feed.

        Returns
        -------
        str
            RSS feed URL.
        """
        return f"{self._base_url}/feed/"

    def get_faq_url(self) -> str:
        """
        Get the URL of the FAQ page.

        Returns
        -------
        str
            FAQ page URL.
        """
        return f"{self._base_url}/faq/"

    def get_donations_url(self) -> str:
        """
        Get the URL of the donations page.

        Returns
        -------
        str
            Donations page URL.
        """
        return f"{self._base_url}/donations/"

    def get_contacts_url(self) -> str:
        """
        Get the URL of the contacts page.

        Returns
        -------
        str
            Contacts page URL.
        """
        return f"{self._base_url}/contacts/"

    def get_troubleshooting_url(self) -> str:
        """
        Get the URL of the troubleshooting page.

        Returns
        -------
        str
            Troubleshooting page URL.
        """
        return f"{self._base_url}/repacks-troubleshooting/"
