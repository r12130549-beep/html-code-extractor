"""
Async HTML extraction service.
Downloads a webpage's HTML source and optionally beautifies it.
"""
import asyncio
import ipaddress
import os
import socket
from dataclasses import dataclass
from datetime import datetime

import aiohttp
import certifi
import ssl
from bs4 import BeautifulSoup

from config import EXTRACT_DIR, MAX_FILE_SIZE_MB
from utils.validators import normalize_url


# ── SSRF guard ──────────────────────────────────────────────────────────────
_PRIVATE_NETWORKS = [
    ipaddress.ip_network("10.0.0.0/8"),
    ipaddress.ip_network("172.16.0.0/12"),
    ipaddress.ip_network("192.168.0.0/16"),
    ipaddress.ip_network("127.0.0.0/8"),
    ipaddress.ip_network("169.254.0.0/16"),   # link-local
    ipaddress.ip_network("::1/128"),
    ipaddress.ip_network("fc00::/7"),
    ipaddress.ip_network("fe80::/10"),
    ipaddress.ip_network("0.0.0.0/8"),
    ipaddress.ip_network("100.64.0.0/10"),    # CGNAT
    ipaddress.ip_network("192.0.2.0/24"),
    ipaddress.ip_network("198.51.100.0/24"),
    ipaddress.ip_network("203.0.113.0/24"),
    ipaddress.ip_network("240.0.0.0/4"),
]


def _is_private_ip(addr: str) -> bool:
    try:
        ip = ipaddress.ip_address(addr)
        return any(ip in net for net in _PRIVATE_NETWORKS)
    except ValueError:
        return True  # unparseable → block


def _check_ssrf(hostname: str) -> None:
    """Resolve *hostname* and raise ValueError if any address is private/reserved."""
    try:
        addrs = socket.getaddrinfo(hostname, None)
    except socket.gaierror as e:
        raise ValueError(f"Could not resolve hostname '{hostname}': {e}") from e
    for info in addrs:
        ip_str = info[4][0]
        if _is_private_ip(ip_str):
            raise ValueError(
                f"Requests to internal/private addresses are not allowed "
                f"(resolved '{hostname}' → {ip_str})."
            )


@dataclass
class ExtractionResult:
    success: bool
    url: str
    filename: str
    filepath: str | None
    file_size: int | None
    status_code: int | None
    headers: dict | None
    error: str | None
    elapsed_ms: float


async def extract_html(
    url: str,
    *,
    filename: str = "extract.html",
    encoding: str = "utf-8",
    include_headers: bool = False,
    beautify: bool = False,
    timeout: int = 30,
    user_id: int = 0,
) -> ExtractionResult:
    """
    Download the HTML from *url* and save to disk.

    Returns an :class:`ExtractionResult` describing the outcome.
    """
    url = normalize_url(url)
    start = datetime.now()

    # SSRF guard — resolve and block private/internal addresses
    from urllib.parse import urlparse as _urlparse
    _hostname = _urlparse(url).hostname or ""
    try:
        await asyncio.to_thread(_check_ssrf, _hostname)
    except ValueError as e:
        return ExtractionResult(
            success=False, url=url, filename=filename if filename.endswith(".html") else filename + ".html",
            filepath=None, file_size=None, status_code=None, headers=None,
            error=str(e), elapsed_ms=0.0,
        )

    ssl_ctx = ssl.create_default_context(cafile=certifi.where())
    connector = aiohttp.TCPConnector(ssl=ssl_ctx)

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0 Safari/537.36"
        ),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
    }

    # Unique filename per user to avoid collisions
    safe_name = filename if filename.endswith(".html") else filename + ".html"
    filepath = os.path.join(EXTRACT_DIR, f"{user_id}_{safe_name}")

    try:
        timeout_obj = aiohttp.ClientTimeout(total=timeout)
        async with aiohttp.ClientSession(
            connector=connector, timeout=timeout_obj, headers=headers
        ) as session:
            async with session.get(url, allow_redirects=True) as resp:
                status_code = resp.status
                resp_headers = dict(resp.headers)

                if status_code >= 400:
                    elapsed = (datetime.now() - start).total_seconds() * 1000
                    return ExtractionResult(
                        success=False,
                        url=url,
                        filename=safe_name,
                        filepath=None,
                        file_size=None,
                        status_code=status_code,
                        headers=resp_headers,
                        error=f"HTTP {status_code}: {resp.reason}",
                        elapsed_ms=elapsed,
                    )

                raw_bytes = await resp.read()

                # Check size limit
                max_bytes = MAX_FILE_SIZE_MB * 1024 * 1024
                if len(raw_bytes) > max_bytes:
                    elapsed = (datetime.now() - start).total_seconds() * 1000
                    return ExtractionResult(
                        success=False,
                        url=url,
                        filename=safe_name,
                        filepath=None,
                        file_size=len(raw_bytes),
                        status_code=status_code,
                        headers=resp_headers,
                        error=f"File too large ({len(raw_bytes) / 1024 / 1024:.1f} MB > {MAX_FILE_SIZE_MB} MB limit)",
                        elapsed_ms=elapsed,
                    )

                # Decode + optional transform in a thread (CPU/blocking work)
                def _prepare_html() -> str:
                    try:
                        text = raw_bytes.decode(encoding, errors="replace")
                    except LookupError:
                        text = raw_bytes.decode("utf-8", errors="replace")
                    if beautify:
                        soup = BeautifulSoup(text, "lxml")
                        text = soup.prettify()
                    if include_headers:
                        header_lines = "\n".join(
                            f"  {k}: {v}" for k, v in resp_headers.items()
                        )
                        text = f"<!--\nResponse Headers:\n{header_lines}\n-->\n\n" + text
                    return text

                html_text = await asyncio.to_thread(_prepare_html)

                # Write to disk in a thread (blocking I/O)
                def _write_file() -> None:
                    with open(filepath, "w", encoding=encoding, errors="replace") as fh:
                        fh.write(html_text)

                await asyncio.to_thread(_write_file)

                file_size = os.path.getsize(filepath)
                elapsed = (datetime.now() - start).total_seconds() * 1000

                return ExtractionResult(
                    success=True,
                    url=url,
                    filename=safe_name,
                    filepath=filepath,
                    file_size=file_size,
                    status_code=status_code,
                    headers=resp_headers,
                    error=None,
                    elapsed_ms=elapsed,
                )

    except aiohttp.ClientConnectorError as e:
        elapsed = (datetime.now() - start).total_seconds() * 1000
        return ExtractionResult(
            success=False, url=url, filename=safe_name, filepath=None,
            file_size=None, status_code=None, headers=None,
            error=f"Connection failed: {e}", elapsed_ms=elapsed,
        )
    except aiohttp.ServerTimeoutError:
        elapsed = (datetime.now() - start).total_seconds() * 1000
        return ExtractionResult(
            success=False, url=url, filename=safe_name, filepath=None,
            file_size=None, status_code=None, headers=None,
            error=f"Request timed out after {timeout}s", elapsed_ms=elapsed,
        )
    except ssl.SSLError as e:
        elapsed = (datetime.now() - start).total_seconds() * 1000
        return ExtractionResult(
            success=False, url=url, filename=safe_name, filepath=None,
            file_size=None, status_code=None, headers=None,
            error=f"SSL error: {e}", elapsed_ms=elapsed,
        )
    except Exception as e:
        elapsed = (datetime.now() - start).total_seconds() * 1000
        return ExtractionResult(
            success=False, url=url, filename=safe_name, filepath=None,
            file_size=None, status_code=None, headers=None,
            error=str(e), elapsed_ms=elapsed,
        )
