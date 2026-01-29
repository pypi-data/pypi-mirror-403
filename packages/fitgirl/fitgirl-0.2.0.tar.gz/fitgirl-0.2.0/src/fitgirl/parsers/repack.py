"""
FitGirl Scraper DOM Parsers - Repack Detail.

Parsers for individual repack pages with full detail extraction.
"""

from __future__ import annotations

import re

from selectolax.parser import Node

from fitgirl.exceptions import ParseError
from fitgirl.models import (
    DownloadMirror,
    DownloadPart,
    MagnetLink,
    Repack,
    RepackFeatures,
    RepackItem,
    TorrentSource,
)
from fitgirl.parsers._utils import (
    _extract_slug,
    _parse_datetime,
    _parse_repack_number,
    _safe_attr,
    _safe_text,
)
from selectolax.parser import HTMLParser

__all__ = ["parse_repack_detail"]


def _extract_field_value(content_node: Node, label: str) -> str | None:
    """
    Extract a field value following a label in the content.

    Looks for pattern: "Label: <strong>Value</strong>" or "Label: Value"
    """
    text = content_node.html or ""

    # Try to find the label followed by a value
    pattern = rf"{re.escape(label)}[:\s]*(?:<strong>)?([^<\n]+)(?:</strong>)?"
    match = re.search(pattern, text, re.IGNORECASE)
    if match:
        return match.group(1).strip()
    return None


def _extract_genres(content_node: Node) -> tuple[str, ...]:
    """Extract genre tags from content."""
    genres: list[str] = []

    # Find the "Genres/Tags:" text and extract following links
    html = content_node.html or ""

    # Look for Genres/Tags section
    match = re.search(
        r"Genres/Tags:.*?(?=Companies:|Languages:|$)", html, re.IGNORECASE | re.DOTALL
    )
    if match:
        section = match.group(0)
        # Extract link texts
        link_pattern = r"<a[^>]*>([^<]+)</a>"
        for link_match in re.finditer(link_pattern, section):
            genre = link_match.group(1).strip()
            if genre:
                genres.append(genre)

    return tuple(genres)


def _extract_companies(content_node: Node) -> tuple[str, ...]:
    """Extract company names from content."""
    html = content_node.html or ""

    # Companies line typically: Companies: Name1, Name2<br>
    match = re.search(
        r"Companies?:\s*([^<]+?)(?:<br|</?p|Languages:)", html, re.IGNORECASE
    )
    if match:
        companies_text = match.group(1).strip()
        # Split by comma and clean up
        return tuple(c.strip() for c in companies_text.split(",") if c.strip())
    return ()


def _extract_languages(content_node: Node) -> str | None:
    """Extract languages string from content."""
    html = content_node.html or ""

    # Languages line typically: Languages: RUS/ENG/MULTI14<br>
    match = re.search(r"Languages?:\s*([A-Z0-9/]+(?:/[A-Z0-9]+)*)", html, re.IGNORECASE)
    if match:
        return match.group(1).strip()
    return None


def _extract_size(content_node: Node, label: str) -> str | None:
    """Extract a size value (Original Size or Repack Size)."""
    html = content_node.html or ""

    # Size lines: Original Size: 66.4 GB or Repack Size: from 47.4 GB [Selective Download]
    pattern = rf"{re.escape(label)}:?\s*((?:from\s+)?\d+(?:\.\d+)?\s*(?:GB|MB|TB)(?:\s*\[Selective Download\])?)"
    match = re.search(pattern, html, re.IGNORECASE)
    if match:
        return match.group(1).strip()
    return None


def _extract_download_mirrors(content_node: Node) -> tuple[DownloadMirror, ...]:
    """Extract direct download mirrors from content."""
    mirrors: list[DownloadMirror] = []

    # Find the Download Mirrors (Direct Links) section
    html = content_node.html or ""

    # Look for the section header and extract following list
    direct_section_match = re.search(
        r"Download Mirrors \(Direct Links\).*?(?=Download Mirrors \(Torrent\)|Repack Features|$)",
        html,
        re.IGNORECASE | re.DOTALL,
    )

    if not direct_section_match:
        return ()

    section = direct_section_match.group(0)

    # Parse each filehoster entry
    # Pattern: Filehoster: Name (Description)
    filehoster_pattern = r"Filehoster:\s*([^\(\<]+)(?:\(([^)]+)\))?"
    link_pattern = r'<a[^>]*href="([^"]+)"[^>]*>([^<]*)</a>'

    current_mirror_name = None
    current_description = None
    current_parts: list[DownloadPart] = []

    lines = section.split("\n")
    for line in lines:
        # Check for new filehoster
        fh_match = re.search(filehoster_pattern, line, re.IGNORECASE)
        if fh_match:
            # Save previous mirror if exists
            if current_mirror_name and current_parts:
                mirrors.append(
                    DownloadMirror(
                        name=current_mirror_name,
                        description=current_description,
                        parts=tuple(current_parts),
                    )
                )
            current_mirror_name = fh_match.group(1).strip()
            current_description = (
                fh_match.group(2).strip() if fh_match.group(2) else None
            )
            current_parts = []

        # Extract download links
        for link_match in re.finditer(link_pattern, line):
            url = link_match.group(1)
            text = link_match.group(2).strip()

            # Skip non-download links
            if "fitgirl-repacks.site" in url:
                continue

            # Try to extract part number
            part_match = re.search(r"(?:part|pt)?\s*(\d+)", text, re.IGNORECASE)
            part_num = (
                int(part_match.group(1)) if part_match else len(current_parts) + 1
            )

            current_parts.append(
                DownloadPart(
                    part_number=part_num,
                    url=url,
                )
            )

    # Save last mirror
    if current_mirror_name and current_parts:
        mirrors.append(
            DownloadMirror(
                name=current_mirror_name,
                description=current_description,
                parts=tuple(current_parts),
            )
        )

    return tuple(mirrors)


def _extract_torrent_sources(content_node: Node) -> tuple[TorrentSource, ...]:
    """Extract torrent sources with magnet links."""
    sources: list[TorrentSource] = []

    html = content_node.html or ""

    # Find the Download Mirrors (Torrent) section
    torrent_section_match = re.search(
        r"Download Mirrors \(Torrent\)(.*?)(?=Repack Features|Game Updates|$)",
        html,
        re.IGNORECASE | re.DOTALL,
    )

    if not torrent_section_match:
        return ()

    section = torrent_section_match.group(1)

    # Parse list items - each typically contains a tracker name, magnet, and torrent link
    # Pattern for tracker entries
    tracker_pattern = r'<a[^>]*href="([^"]+)"[^>]*>([^<]+)</a>'

    for match in re.finditer(tracker_pattern, section):
        url = match.group(1)
        name = match.group(2).strip()

        # Skip if it's a magnet or torrent file link (we handle those separately)
        if url.startswith("magnet:") or "paste.fitgirl-repacks.site" in url:
            continue

        # Skip internal links
        if "fitgirl-repacks.site" in url and "paste." not in url:
            continue

        # Find the associated magnet link (usually follows immediately)
        # Look for magnet link after this tracker
        magnet_match = re.search(
            rf'{re.escape(url)}.*?<a[^>]*href="(magnet:\?[^"]+)"',
            section,
            re.DOTALL,
        )
        magnet = None
        if magnet_match:
            try:
                magnet = MagnetLink.from_uri(magnet_match.group(1))
            except ValueError:
                pass

        # Find associated torrent file link
        torrent_file_match = re.search(
            rf'{re.escape(url)}.*?<a[^>]*href="(https://paste\.fitgirl-repacks\.site[^"]+)"',
            section,
            re.DOTALL,
        )
        torrent_file_url = torrent_file_match.group(1) if torrent_file_match else None

        sources.append(
            TorrentSource(
                name=name,
                page_url=url,
                magnet=magnet,
                torrent_file_url=torrent_file_url,
            )
        )

    return tuple(sources)


def _extract_repack_features(content_node: Node) -> RepackFeatures:
    """Extract and parse repack features."""
    html = content_node.html or ""

    # Find the Repack Features section
    features_match = re.search(
        r"Repack Features(.*?)(?=<h3|$)",
        html,
        re.IGNORECASE | re.DOTALL,
    )

    if not features_match:
        return RepackFeatures()

    section = features_match.group(1)

    # Extract list items
    li_pattern = r"<li>([^<]+(?:<[^>]+>[^<]*</[^>]+>)*[^<]*)</li>"
    raw_features: list[str] = []

    for match in re.finditer(li_pattern, section, re.DOTALL):
        # Strip HTML tags
        text = re.sub(r"<[^>]+>", "", match.group(1)).strip()
        if text:
            raw_features.append(text)

    # Parse specific features
    based_on = None
    game_version = None
    is_lossless = False
    is_md5_perfect = False
    selective_download = False
    compression_info = None
    install_time_min = None
    install_time_max = None
    hdd_space = None
    ram_required = None
    dlcs: list[str] = []
    notes: list[str] = []

    for feature in raw_features:
        lower = feature.lower()

        if "based on" in lower:
            based_on = feature
        elif "game version" in lower or re.match(r"v\d+", feature):
            game_version = feature
        elif "100% lossless" in lower:
            is_lossless = True
        elif "md5 perfect" in lower:
            is_md5_perfect = True
        elif "selective download" in lower:
            selective_download = True
        elif "compressed from" in lower:
            compression_info = feature
        elif "installation takes" in lower:
            # Try to extract min/max times
            time_match = re.search(
                r"from\s+(.+?)\s+up to\s+(.+)", feature, re.IGNORECASE
            )
            if time_match:
                install_time_min = time_match.group(1)
                install_time_max = time_match.group(2)
            else:
                install_time_min = feature
        elif "hdd space" in lower:
            hdd_space = feature
        elif "ram" in lower and "required" in lower:
            ram_required = feature
        elif "dlc" in lower or "included" in lower:
            dlcs.append(feature)
        else:
            notes.append(feature)

    return RepackFeatures(
        based_on=based_on,
        game_version=game_version,
        dlcs_included=tuple(dlcs),
        is_lossless=is_lossless,
        is_md5_perfect=is_md5_perfect,
        selective_download=selective_download,
        compression_info=compression_info,
        install_time_min=install_time_min,
        install_time_max=install_time_max,
        hdd_space_after_install=hdd_space,
        ram_required=ram_required,
        notes=tuple(notes),
        raw_features=tuple(raw_features),
    )


def _extract_screenshots(content_node: Node) -> tuple[str, ...]:
    """Extract screenshot URLs from content."""
    screenshots: list[str] = []

    # Look for images in lightbox/gallery links
    for a in content_node.css("a[href*='screenshot'], a[href*='Screen'], a.lightbox"):
        href = a.attributes.get("href", "")
        if href and not href.startswith("magnet:"):
            screenshots.append(href)

    # Also look for direct image links
    for img in content_node.css("img"):
        src = img.attributes.get("src", "")
        if src and ("screenshot" in src.lower() or "screen" in src.lower()):
            screenshots.append(src)

    return tuple(dict.fromkeys(screenshots))  # Remove duplicates while preserving order


def _extract_riotpixels_url(content_node: Node) -> str | None:
    """Extract RiotPixels URL from content."""
    for a in content_node.css("a"):
        href = a.attributes.get("href")
        if href and "riotpixels.com" in href:
            return href
    return None


def _extract_cs_rin_url(content_node: Node) -> str | None:
    """Extract CS.RIN.RU discussion URL from content."""
    for a in content_node.css("a"):
        href = a.attributes.get("href")
        if href and "cs.rin.ru" in href:
            return href
    return None


def _extract_related_repacks(content_node: Node) -> tuple[RepackItem, ...]:
    """Extract related repacks from the 'You might also like' section."""
    related: list[RepackItem] = []

    # Check for Jetpack related posts
    related_div = content_node.css_first("div#jp-relatedposts, div.jp-relatedposts")
    if not related_div:
        return ()

    for item in related_div.css("div.jp-relatedposts-post"):
        title_node = item.css_first("h4.jp-relatedposts-post-title a")
        if not title_node:
            continue

        href = title_node.attributes.get("href")
        title = title_node.text(strip=True)

        # Extract thumbnail if available
        img = item.css_first("img")
        thumbnail = img.attributes.get("src") if img else None

        if href and title:
            from fitgirl.parsers._utils import _extract_slug

            slug = _extract_slug(href)

            related.append(
                RepackItem(
                    title=title,
                    slug=slug,
                    url=href,
                    thumbnail_url=thumbnail,
                )
            )

    return tuple(related)


def _extract_cover_url(content_node: Node) -> str | None:
    """Extract high-res cover URL."""
    # Look for the main image, oftentimes it's the first image in content
    # or inside a paragraph, possibly with a link to full size

    # Try 1: Image inside a link (often leads to full size)
    img_link = content_node.css_first(
        "p a[href$='.jpg'], p a[href$='.png'], div.entry-content > a[href$='.jpg']"
    )
    if img_link:
        return img_link.attributes.get("href")

    # Try 2: First valid image source
    # Exclude small icons or known UI elements if possible, but first image is usually cover
    img = content_node.css_first("div.entry-content img")
    if img:
        # If wrapped in link, prefer link
        if img.parent and img.parent.tag == "a":
            href = img.parent.attributes.get("href")
            if href and (href.endswith(".jpg") or href.endswith(".png")):
                return href
        return img.attributes.get("src")

    return None


def parse_repack_detail(html: bytes, url: str) -> Repack:
    """
    Parse a repack detail page.

    Parameters
    ----------
    html
        Raw HTML content as bytes.
    url
        The URL of this repack page.

    Returns
    -------
    Repack
        Fully parsed repack with all available data.
    """
    tree = HTMLParser(html)
    slug = _extract_slug(url)

    # Find the main article
    article = tree.css_first("article.post")
    if article is None:
        raise ParseError("No article found on repack page", url=url)

    # Extract title
    title_elem = article.css_first("h1.entry-title")
    title = _safe_text(title_elem) if title_elem else slug

    # Extract date
    time_elem = article.css_first("time.entry-date")
    date_str = _safe_attr(time_elem, "datetime")
    date = _parse_datetime(date_str) if date_str else None

    # Extract author
    author_elem = article.css_first("span.author a")
    author = _safe_text(author_elem) if author_elem else None

    # Get the content div
    content = article.css_first("div.entry-content")
    if content is None:
        raise ParseError("No content found on repack page", url=url)

    # Extract repack number from h3 header
    h3 = content.css_first("h3")
    h3_text = _safe_text(h3) if h3 else ""
    repack_number, is_updated = _parse_repack_number(h3_text)

    # Extract all fields
    genres = _extract_genres(content)
    companies = _extract_companies(content)
    languages = _extract_languages(content)
    original_size = _extract_size(content, "Original Size")
    repack_size = _extract_size(content, "Repack Size")
    download_mirrors = _extract_download_mirrors(content)
    torrent_sources = _extract_torrent_sources(content)
    repack_features = _extract_repack_features(content)
    screenshots = _extract_screenshots(content)
    riotpixels_url = _extract_riotpixels_url(content)
    cs_rin_url = _extract_cs_rin_url(content)
    related_repacks = _extract_related_repacks(content)
    cover_url = _extract_cover_url(content)

    # Extract categories
    cat_links = article.css("span.cat-links a")
    categories = tuple(_safe_text(a) for a in cat_links if _safe_text(a))

    # Extract tags
    tag_links = article.css("footer.entry-meta a[rel='tag']")
    tags = tuple(_safe_text(a) for a in tag_links if _safe_text(a))

    # Extract description (paragraphs after features, before footer)
    description_parts: list[str] = []
    for p in content.css("p"):
        text = _safe_text(p)
        # Skip if it's metadata or download section
        if any(
            x in text.lower()
            for x in [
                "genres/tags",
                "companies",
                "languages",
                "original size",
                "download",
            ]
        ):
            continue
        if text and len(text) > 50:  # Only include substantial paragraphs
            description_parts.append(text)
    description = "\n\n".join(description_parts) if description_parts else None

    return Repack(
        title=title,
        slug=slug,
        url=url,
        repack_number=repack_number,
        is_updated=is_updated,
        date=date,
        author=author,
        riotpixels_url=riotpixels_url,
        genres=genres,
        companies=companies,
        languages=languages,
        original_size=original_size,
        repack_size=repack_size,
        download_mirrors=download_mirrors,
        torrent_sources=torrent_sources,
        repack_features=repack_features,
        screenshots=screenshots,
        description=description,
        categories=categories,
        tags=tags,
        cs_rin_url=cs_rin_url,
        related_repacks=related_repacks,
        cover_url=cover_url,
    )
