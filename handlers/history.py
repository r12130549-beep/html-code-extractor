"""
/history command handler — view and clear extraction history.
"""
from telegram import Update
from telegram.ext import ContextTypes
from telegram.constants import ParseMode

from database.db import get_history, upsert_user
from keyboards.main_keyboard import history_keyboard, back_home_keyboard
from utils.helpers import format_file_size, format_datetime, status_icon, truncate
from utils.logger import logger


def _build_history_text(entries: list[dict]) -> str:
    if not entries:
        return """
╔══════════════════════════════╗
║     📂  YOUR HISTORY         ║
╚══════════════════════════════╝

<i>No extractions yet.</i>

Use <code>/html https://example.com</code> to get started!
""".strip()

    lines = [
        "╔══════════════════════════════╗",
        "║     📂  YOUR HISTORY         ║",
        "╚══════════════════════════════╝",
        "",
        f"Showing last <b>{len(entries)}</b> extractions:",
        "━━━━━━━━━━━━━━━━━━━━━━━━━━",
    ]
    for i, entry in enumerate(entries, 1):
        icon = status_icon(entry["status"])
        url_short = truncate(entry["url"], 38)
        size_str = format_file_size(entry["file_size"]) if entry["file_size"] else "—"
        dt_str = entry["created_at"][:16].replace("T", " ")
        lines += [
            f"<b>{i}.</b> {icon} <code>{url_short}</code>",
            f"    📄 {entry['filename']}  |  💾 {size_str}  |  🕒 {dt_str}",
        ]
        if i < len(entries):
            lines.append("─────────────────────────────")

    return "\n".join(lines)


async def history_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    await upsert_user(user.id, user.username, user.first_name)
    entries = await get_history(user.id)
    logger.info("User %s viewed history (%d entries)", user.id, len(entries))
    await update.message.reply_text(
        _build_history_text(entries),
        parse_mode=ParseMode.HTML,
        reply_markup=history_keyboard(bool(entries)),
    )
