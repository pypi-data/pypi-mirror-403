"""
FitGirl Scraper DOM Parsers.

High-performance HTML parsing using selectolax with defensive extraction
patterns for robustness against DOM structure changes.

This package provides a modular structure with parsers organized by function:
- listing: Listing pages and search results
- repack: Individual repack detail pages
- special: Popular repacks, updates digest, A-Z list
- api: WordPress REST API response parsing
"""

from __future__ import annotations

# Listing parsers
from fitgirl.parsers.listing import parse_listing_page, parse_search_results

# Repack detail parser
from fitgirl.parsers.repack import parse_repack_detail

# Special page parsers
from fitgirl.parsers.special import (
    parse_az_list,
    parse_donation_info,
    parse_popular_repacks,
    parse_updates_digest,
)

# API parsers
from fitgirl.parsers.api import (
    parse_listing_from_api_posts,
    parse_repack_from_api_post,
)

__all__ = [
    "parse_listing_page",
    "parse_search_results",
    "parse_repack_detail",
    "parse_popular_repacks",
    "parse_updates_digest",
    "parse_az_list",
    "parse_donation_info",
    "parse_repack_from_api_post",
    "parse_listing_from_api_posts",
]
