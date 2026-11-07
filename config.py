"""
Configuration module for the HTML Extractor Bot.
"""
import os
from dotenv import load_dotenv

load_dotenv()

# ─── Bot credentials ────────────────────────────────────────────────────────
BOT_TOKEN: str = os.environ.get("TELEGRAM_BOT_TOKEN", "")

# Admin user IDs (comma-separated in env). Example: "123456789,987654321"
_admin_ids_raw: str = os.environ.get("ADMIN_IDS", "")
ADMIN_IDS: list[int] = (
    [int(x.strip()) for x in _admin_ids_raw.split(",") if x.strip()]
    if _admin_ids_raw.strip()
    else []
)

# ─── Paths ──────────────────────────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOGS_DIR = os.path.join(BASE_DIR, "logs")
TEMP_DIR = os.path.join(BASE_DIR, "temp")
EXTRACT_DIR = os.path.join(BASE_DIR, "extract")
DB_PATH = os.path.join(BASE_DIR, "database", "bot.db")

# Create required directories
for _dir in (LOGS_DIR, TEMP_DIR, EXTRACT_DIR, os.path.dirname(DB_PATH)):
    os.makedirs(_dir, exist_ok=True)

# ─── Default user settings ──────────────────────────────────────────────────
DEFAULT_SETTINGS: dict = {
    "output_filename": "extract.html",
    "encoding": "utf-8",
    "include_headers": False,
    "beautify_html": False,
    "auto_delete": True,
    "timeout": 30,
}

# ─── Bot behaviour ──────────────────────────────────────────────────────────
MAX_HISTORY_ENTRIES = 50   # max stored per user
MAX_FILE_SIZE_MB = 50      # refuse files larger than this
REQUEST_TIMEOUT_MAX = 120  # seconds
BOT_VERSION = "1.0.0"
BOT_NAME = "HTML Extractor Pro"
DEVELOPER_LINK = "https://t.me/HTMLExtractorBot"
