"""
FitGirl Scraper Data Models - Donation.

Donation information models.
"""

from __future__ import annotations

import msgspec

__all__ = ["DonationInfo"]


class DonationInfo(msgspec.Struct, frozen=True, kw_only=True):
    """
    Donation information and crypto addresses.

    Attributes
    ----------
    btc_address
        Bitcoin wallet address.
    xmr_address
        Monero wallet address.
    description
        Donation related text/notes.
    """

    btc_address: str | None = None
    xmr_address: str | None = None
    description: str | None = None
