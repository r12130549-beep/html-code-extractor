"""
URL validation utilities.
"""
import re
from urllib.parse import urlparse


# Regex for a valid HTTP/HTTPS URL
_URL_RE = re.compile(
    r"^(https?://)?"                        # scheme (optional)
    r"(([a-zA-Z0-9\-]+\.)+[a-zA-Z]{2,})"   # domain
    r"(:\d+)?"                              # optional port
    r"(/[^\s]*)?"                           # optional path
    r"$",
    re.IGNORECASE,
)


def is_valid_url(url: str) -> bool:
    """Return True if *url* looks like a valid HTTP/HTTPS URL."""
    url = url.strip()
    if not url:
        return False

    # Prepend scheme if missing so urlparse works
    if not url.startswith(("http://", "https://")):
        url = "https://" + url

    try:
        parsed = urlparse(url)
        return bool(parsed.scheme and parsed.netloc and _URL_RE.match(url))
    except Exception:
        return False


def normalize_url(url: str) -> str:
    """Ensure the URL has a scheme. Returns the normalized URL."""
    url = url.strip()
    if not url.startswith(("http://", "https://")):
        url = "https://" + url
    return url
