"""
Formatting and helper utilities.
"""
from datetime import datetime


def format_file_size(size_bytes: int) -> str:
    """Return a human-readable file size string."""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 ** 2:
        return f"{size_bytes / 1024:.1f} KB"
    elif size_bytes < 1024 ** 3:
        return f"{size_bytes / 1024 ** 2:.2f} MB"
    return f"{size_bytes / 1024 ** 3:.2f} GB"


def format_datetime(dt: datetime | None = None) -> str:
    """Return a formatted datetime string."""
    if dt is None:
        dt = datetime.now()
    return dt.strftime("%Y-%m-%d %H:%M:%S")


def truncate(text: str, max_len: int = 40) -> str:
    """Truncate a string and append '…' if it exceeds max_len."""
    return text if len(text) <= max_len else text[: max_len - 1] + "…"


def status_icon(status: str) -> str:
    """Return an emoji representing a request status."""
    return {"success": "✅", "failed": "❌", "timeout": "⏱"}.get(status, "❓")


def bool_display(value: bool) -> str:
    """Return ✅ / ❌ for boolean settings."""
    return "✅ Enabled" if value else "❌ Disabled"
