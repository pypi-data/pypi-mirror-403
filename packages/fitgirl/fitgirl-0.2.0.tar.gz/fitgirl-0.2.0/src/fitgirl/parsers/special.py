"""
FitGirl Scraper DOM Parsers - Special Pages.

Parsers for special pages: popular repacks, updates digest, A-Z list.
"""

from __future__ import annotations

from selectolax.parser import HTMLParser

from fitgirl.models import DonationInfo, PopularRepack, RepackItem, UpdateDigestEntry
from fitgirl.parsers._utils import _extract_slug, _safe_attr, _safe_text

__all__ = [
    "parse_popular_repacks",
    "parse_updates_digest",
    "parse_az_list",
    "parse_donation_info",
]


def parse_popular_repacks(html: bytes) -> list[PopularRepack]:
    """
    Parse a popular repacks page (monthly or yearly).

    Parameters
    ----------
    html
        Raw HTML content as bytes.

    Returns
    -------
    list[PopularRepack]
        List of popular repacks with rankings.
    """
    tree = HTMLParser(html)
    repacks: list[PopularRepack] = []

    # Find the content div
    content = tree.css_first("div.entry-content, article.post div.entry-content")
    if content is None:
        return repacks

    # Look for ordered list or numbered entries
    rank = 1
    for li in content.css("ol li, li"):
        link = li.css_first("a")
        if link is None:
            continue

        title = _safe_text(link)
        url = _safe_attr(link, "href")

        if not title or not url or "fitgirl-repacks.site" not in url:
            continue

        slug = _extract_slug(url)

        repacks.append(
            PopularRepack(
                rank=rank,
                title=title,
                slug=slug,
                url=url,
            )
        )
        rank += 1

    return repacks


def parse_updates_digest(html: bytes) -> list[UpdateDigestEntry]:
    """
    Parse an updates digest page.

    Parameters
    ----------
    html
        Raw HTML content as bytes.

    Returns
    -------
    list[UpdateDigestEntry]
        List of update entries.
    """
    tree = HTMLParser(html)
    entries: list[UpdateDigestEntry] = []

    content = tree.css_first("div.entry-content")
    if content is None:
        return entries

    # Updates are typically in list items
    for li in content.css("li"):
        link = li.css_first("a")
        if link is None:
            continue

        title = _safe_text(link)
        url = _safe_attr(link, "href")

        if not title or not url:
            continue

        slug = _extract_slug(url)

        # Try to get update info from surrounding text
        full_text = _safe_text(li)
        update_info = full_text.replace(title, "").strip(" -–—:\n") or None

        entries.append(
            UpdateDigestEntry(
                title=title,
                slug=slug,
                url=url,
                update_info=update_info,
            )
        )

    return entries


def parse_az_list(html: bytes) -> list[RepackItem]:
    """
    Parse the A-Z list page.

    Parameters
    ----------
    html
        Raw HTML content as bytes.

    Returns
    -------
    list[RepackItem]
        List of all repacks from A-Z.
    """
    tree = HTMLParser(html)
    items: list[RepackItem] = []

    content = tree.css_first("div.entry-content")
    if content is None:
        return items

    # A-Z list typically has links in paragraphs or lists
    for a in content.css("a"):
        url = _safe_attr(a, "href")
        title = _safe_text(a)

        if not url or not title:
            continue

        # Filter to only repack pages
        if "fitgirl-repacks.site" not in url:
            continue

        # Skip navigation/category links
        if any(
            x in url
            for x in ["/tag/", "/category/", "/page/", "?s=", "/faq", "/donations"]
        ):
            continue

        slug = _extract_slug(url)
        if not slug:
            continue

        items.append(
            RepackItem(
                title=title,
                slug=slug,
                url=url,
            )
        )

    return items


def parse_donation_info(html: bytes) -> DonationInfo:
    """
    Parse the donations page.

    Parameters
    ----------
    html
        Raw HTML content as bytes.

    Returns
    -------
    DonationInfo
        Donation addresses and info.
    """
    tree = HTMLParser(html)

    btc_address = None
    xmr_address = None
    description_parts = []

    content = tree.css_first("div.entry-content")
    if content:
        # Extract text content
        for p in content.css("p, blockquote"):
            text = _safe_text(p)
            if not text:
                continue

            # Naive heuristics for addresses
            if "BTC" in text or "Bitcoin" in text:
                # Try to extract address: usually starts with 1, 3, or bc1 and is long
                import re

                match = re.search(
                    r"\b(1[a-km-zA-Z1-9]{25,34}|3[a-km-zA-Z1-9]{25,34}|bc1[a-zA-Z0-9]{39,59})\b",
                    text,
                )
                if match:
                    btc_address = match.group(0)

            if "XMR" in text or "Monero" in text:
                # Monero addresses start with 4 or 8 and are 95 chars long
                import re

                match = re.search(
                    r"\b(4[0-9AB][1-9A-HJ-NP-Za-km-z]{93}|8[0-9AB][1-9A-HJ-NP-Za-km-z]{93})\b",
                    text,
                )
                if match:
                    xmr_address = match.group(0)

            description_parts.append(text)

    return DonationInfo(
        btc_address=btc_address,
        xmr_address=xmr_address,
        description="\n\n".join(description_parts) if description_parts else None,
    )
