"""
FitGirl Scraper Tracker Utilities.

Provides functionality for scraping UDP/HTTP trackers to get torrent health.
"""

from __future__ import annotations

import asyncio
import random
import struct
import time
from typing import TYPE_CHECKING
from urllib.parse import urlparse

from fitgirl.models.torrent import TorrentHealth

if TYPE_CHECKING:
    from fitgirl.models.torrent import MagnetLink


class TrackerClient:
    """
    Client for scraping BitTorrent trackers.

    Supports UDP tracker protocol for efficient batch health checking.
    """

    def __init__(self, timeout: float = 3.0, retries: int = 2) -> None:
        self.timeout = timeout
        self.retries = retries

    async def check_health(self, magnet: MagnetLink) -> TorrentHealth | None:
        """
        Check health for a magnet link by querying its trackers.

        Returns the best result (highest seed count) from all working trackers.
        """
        tasks = []
        for tracker_url in magnet.trackers:
            if tracker_url.startswith("udp://"):
                tasks.append(self._scrape_udp(tracker_url, magnet.info_hash))

        if not tasks:
            return None

        # Gather all results
        results = await asyncio.gather(*tasks, return_exceptions=True)

        best_health: TorrentHealth | None = None

        for res in results:
            if isinstance(res, TorrentHealth):
                if best_health is None or res.seeds > best_health.seeds:
                    best_health = res

        return best_health

    async def _scrape_udp(self, tracker_url: str, info_hash: str) -> TorrentHealth:
        """
        Scrape a UDP tracker for a single info_hash.

        Implements the UDP tracker protocol (BEP 15).
        """
        parsed = urlparse(tracker_url)
        host = parsed.hostname
        port = parsed.port

        if not host or not port:
            raise ValueError(f"Invalid UDP tracker URL: {tracker_url}")

        # Connection ID constant
        protocol_id = 0x41727101980

        # Create UDP socket
        loop = asyncio.get_running_loop()

        # We need a custom protocol to handle the async UDP communication
        transport, protocol = await loop.create_datagram_endpoint(
            lambda: UDPTrackerProtocol(), remote_addr=(host, port)
        )

        try:
            # 1. Connect Request
            trans_id_connect = random.randint(0, 65535)
            action_connect = 0  # Connect

            connect_req = struct.pack(
                "!QII", protocol_id, action_connect, trans_id_connect
            )
            protocol.send(connect_req)

            # Wait for Connect Response
            data = await asyncio.wait_for(protocol.recv(), timeout=self.timeout)

            if len(data) < 16:
                raise RuntimeError("Invalid connect response length")

            action_res, trans_id_res, conn_id = struct.unpack("!IIQ", data[:16])

            if action_res != 0 or trans_id_res != trans_id_connect:
                raise RuntimeError("Invalid connect response data")

            # 2. Scrape Request
            trans_id_scrape = random.randint(0, 65535)
            action_scrape = 2  # Scrape

            # Info hash must be bytes
            info_hash_bytes = bytes.fromhex(info_hash)

            scrape_req = (
                struct.pack("!QII", conn_id, action_scrape, trans_id_scrape)
                + info_hash_bytes
            )
            protocol.send(scrape_req)

            # Wait for Scrape Response
            data = await asyncio.wait_for(protocol.recv(), timeout=self.timeout)

            if len(data) < 8:
                raise RuntimeError("Invalid scrape response length")

            action_res, trans_id_res = struct.unpack("!II", data[:8])

            if action_res != 2 or trans_id_res != trans_id_scrape:
                raise RuntimeError("Invalid scrape response data")

            # Parse stats (seeders, completed, leechers) -> 12 bytes per hash
            if len(data) < 20:
                raise RuntimeError("No scrape data returned")

            seeders, completed, leechers = struct.unpack("!III", data[8:20])

            return TorrentHealth(
                seeds=seeders,
                peers=leechers,
                downloaded=completed,
                last_updated=time.time(),
            )

        except Exception as e:
            raise RuntimeError(f"UDP Scrape failed: {e}") from e
        finally:
            transport.close()


class UDPTrackerProtocol(asyncio.DatagramProtocol):
    def __init__(self) -> None:
        self.transport: asyncio.DatagramTransport | None = None
        self.future: asyncio.Future[bytes] = asyncio.Future()

    def connection_made(self, transport: asyncio.BaseTransport) -> None:
        self.transport = transport  # type: ignore

    def datagram_received(self, data: bytes, addr: tuple[str, int]) -> None:
        if not self.future.done():
            self.future.set_result(data)

    def error_received(self, exc: Exception) -> None:
        if not self.future.done():
            self.future.set_exception(exc)

    def send(self, data: bytes) -> None:
        if self.transport:
            self.transport.sendto(data)
            self.future = asyncio.Future()  # Reset for next receive

    async def recv(self) -> bytes:
        return await self.future
