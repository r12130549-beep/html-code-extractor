"""
/html command handler — the core extraction flow with animated progress.
"""
import asyncio
import os

from telegram import Update, Message
from telegram.ext import ContextTypes
from telegram.constants import ParseMode

from database.db import upsert_user, add_history, get_settings
from keyboards.main_keyboard import extract_again_keyboard, back_home_keyboard
from services.extractor import extract_html
from utils.helpers import format_file_size
from utils.validators import is_valid_url
from utils.logger import logger


# ── Animated progress frames ────────────────────────────────────────────────
PROGRESS_STEPS = [
    "🌐  <b>Connecting to server…</b>",
    "📥  <b>Downloading HTML source…</b>",
    "📝  <b>Building <code>extract.html</code>…</b>",
    "🚀  <b>Preparing your file…</b>",
]

USAGE_TEXT = """
╔═══════════════════════════════╗
║     🔗  HTML EXTRACTOR        ║
╚═══════════════════════════════╝

Send me a URL to extract its HTML source:

<code>/html https://example.com</code>

I'll download the complete HTML and send it as a file.
""".strip()

INVALID_URL_TEXT = """
╔═══════════════════════════════╗
║     ❌  INVALID URL           ║
╚═══════════════════════════════╝

The URL you provided doesn't look valid.

<b>Correct format:</b>
<code>/html https://example.com</code>
<code>/html http://sub.domain.org/path</code>

Please check your URL and try again.
""".strip()


def _success_text(url: str, filename: str, size: int, elapsed_ms: float) -> str:
    return f"""
╔═══════════════════════════════════╗
║     ✅  EXTRACTION COMPLETE       ║
╚═══════════════════════════════════╝

🌐 <b>URL:</b> <code>{url}</code>
📄 <b>File:</b> <code>{filename}</code>
💾 <b>Size:</b> {format_file_size(size)}
⚡ <b>Time:</b> {elapsed_ms / 1000:.2f}s

<i>Your HTML file is ready — tap the document above to save it.</i>
""".strip()


def _error_text(url: str, error: str) -> str:
    return f"""
╔═══════════════════════════════════╗
║     ❌  EXTRACTION FAILED         ║
╚═══════════════════════════════════╝

🌐 <b>URL:</b> <code>{url}</code>
💬 <b>Reason:</b> {error}

Please check the URL and try again.
""".strip()


async def _animate_progress(msg: Message) -> None:
    """Cycle through progress messages with a small delay between each."""
    for step in PROGRESS_STEPS:
        await asyncio.sleep(0.8)
        try:
            await msg.edit_text(step, parse_mode=ParseMode.HTML)
        except Exception:
            pass


async def html_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    await upsert_user(user.id, user.username, user.first_name)

    # No argument — show usage
    if not context.args:
        await update.message.reply_text(
            USAGE_TEXT,
            parse_mode=ParseMode.HTML,
            reply_markup=back_home_keyboard(),
        )
        return

    url = " ".join(context.args).strip()

    # Validate URL
    if not is_valid_url(url):
        await update.message.reply_text(
            INVALID_URL_TEXT,
            parse_mode=ParseMode.HTML,
            reply_markup=back_home_keyboard(),
        )
        return

    # Start loading screen
    loading_msg = await update.message.reply_text(
        PROGRESS_STEPS[0], parse_mode=ParseMode.HTML
    )
    logger.info("User %s extracting URL: %s", user.id, url)

    # Load user settings
    settings = await get_settings(user.id)

    # Run extraction and progress animation concurrently
    animation_task = asyncio.create_task(_animate_progress(loading_msg))
    result = await extract_html(
        url,
        filename=settings["output_filename"],
        encoding=settings["encoding"],
        include_headers=settings["include_headers"],
        beautify=settings["beautify_html"],
        timeout=settings["timeout"],
        user_id=user.id,
    )
    animation_task.cancel()
    # Await the cancelled task so its CancelledError is properly consumed
    with asyncio.CancelledError.__class__:
        pass
    try:
        await animation_task
    except asyncio.CancelledError:
        pass

    # Record in history
    await add_history(
        user.id,
        url,
        result.filename,
        result.file_size,
        "success" if result.success else "failed",
    )

    if result.success:
        await loading_msg.edit_text(
            "🚀  <b>Uploading file to Telegram…</b>", parse_mode=ParseMode.HTML
        )
        try:
            with open(result.filepath, "rb") as fh:
                await update.message.reply_document(
                    document=fh,
                    filename=result.filename,
                    caption=_success_text(
                        result.url, result.filename, result.file_size, result.elapsed_ms
                    ),
                    parse_mode=ParseMode.HTML,
                    reply_markup=extract_again_keyboard(),
                )
            await loading_msg.delete()
        except Exception as exc:
            logger.error("Failed to send file: %s", exc)
            await loading_msg.edit_text(
                _error_text(url, "Failed to upload the file to Telegram."),
                parse_mode=ParseMode.HTML,
                reply_markup=extract_again_keyboard(),
            )
        finally:
            # Auto-delete temp file if enabled
            if settings["auto_delete"] and result.filepath and os.path.exists(result.filepath):
                try:
                    os.remove(result.filepath)
                except OSError:
                    pass
    else:
        await loading_msg.edit_text(
            _error_text(url, result.error or "Unknown error"),
            parse_mode=ParseMode.HTML,
            reply_markup=extract_again_keyboard(),
        )
