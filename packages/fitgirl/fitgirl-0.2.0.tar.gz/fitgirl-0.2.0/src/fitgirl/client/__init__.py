"""
FitGirl Scraper Client Package.

Primary public API for interacting with fitgirl-repacks.site.

This package provides a modular structure using mixin classes:
- _base: Core infrastructure (init, close, context manager)
- _api: WordPress REST API methods
- _browse: HTML scraping browsing methods
- _special: Special page methods (popular, updates, A-Z)
- _urls: Static URL getters
"""

from __future__ import annotations

from fitgirl.client.client import FitGirlClient

__all__ = ["FitGirlClient"]
