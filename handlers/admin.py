"""
/admin command handler — admin-only panel.
"""
import os
from datetime import datetime

from telegram import Update
from telegram.ext import ContextTypes
from telegram.constants import ParseMode

from config import ADMIN_IDS, LOGS_DIR
from database.db import get_stats, get_all_users
from keyboards.main_keyboard import admin_keyboard, back_home_keyboard
from utils.logger import logger


def _admin_check(user_id: int) -> bool:
    return user_id in ADMIN_IDS


DENIED_TEXT = """
╔══════════════════════════════╗
║     🚫  ACCESS DENIED        ║
╚══════════════════════════════╝

This panel is reserved for bot administrators.
""".strip()

PANEL_TEXT = """
╔══════════════════════════════════╗
║     🛡️  ADMIN PANEL              ║
╚══════════════════════════════════╝

Welcome, Administrator. Choose an option below.
""".strip()


def _stats_text(stats: dict, user_count: int) -> str:
    return f"""
╔══════════════════════════════════╗
║     📊  BOT STATISTICS           ║
╚══════════════════════════════════╝

👥 <b>Total Users:</b>             {user_count}
📨 <b>Total Requests:</b>          {stats.get('total_requests', 0)}
✅ <b>Successful Extractions:</b>  {stats.get('successful_extractions', 0)}
❌ <b>Failed Requests:</b>         {stats.get('failed_requests', 0)}

📅 <b>Report generated:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
""".strip()


def _users_text(users: list[dict]) -> str:
    lines = [
        "╔══════════════════════════════╗",
        "║     👥  USER LIST             ║",
        "╚══════════════════════════════╝",
        "",
        f"Total registered: <b>{len(users)}</b>",
        "━━━━━━━━━━━━━━━━━━━━━━━━━━",
    ]
    for u in users[:20]:  # cap at 20 to avoid huge messages
        uname = f"@{u['username']}" if u["username"] else "—"
        joined = u["joined_at"][:10]
        lines.append(f"• <b>{u['first_name']}</b> ({uname})  ID: <code>{u['user_id']}</code>  📅 {joined}")
    if len(users) > 20:
        lines.append(f"\n<i>… and {len(users) - 20} more</i>")
    return "\n".join(lines)


async def admin_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    if not _admin_check(user.id):
        await update.message.reply_text(DENIED_TEXT, parse_mode=ParseMode.HTML)
        return

    logger.info("Admin %s opened admin panel", user.id)
    await update.message.reply_text(
        PANEL_TEXT,
        parse_mode=ParseMode.HTML,
        reply_markup=admin_keyboard(),
    )


async def handle_admin_stats(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    user = query.from_user

    if not _admin_check(user.id):
        await query.answer("Access denied.", show_alert=True)
        return

    stats = await get_stats()
    users = await get_all_users()
    await query.edit_message_text(
        _stats_text(stats, len(users)),
        parse_mode=ParseMode.HTML,
        reply_markup=back_home_keyboard(),
    )


async def handle_admin_users(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    user = query.from_user

    if not _admin_check(user.id):
        await query.answer("Access denied.", show_alert=True)
        return

    users = await get_all_users()
    await query.edit_message_text(
        _users_text(users),
        parse_mode=ParseMode.HTML,
        reply_markup=back_home_keyboard(),
    )


async def handle_admin_logs(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    user = query.from_user

    if not _admin_check(user.id):
        await query.answer("Access denied.", show_alert=True)
        return

    log_file = os.path.join(LOGS_DIR, "bot.log")
    if not os.path.exists(log_file):
        await query.edit_message_text("No log file found.", reply_markup=back_home_keyboard())
        return

    # Tail last 50 lines (offloaded to thread — blocking I/O)
    def _read_tail() -> str:
        with open(log_file, "r", encoding="utf-8", errors="replace") as fh:
            lines = fh.readlines()
        return "".join(lines[-50:])

    import asyncio as _asyncio
    tail = await _asyncio.to_thread(_read_tail)
    if len(tail) > 3500:
        tail = "…" + tail[-3400:]

    await query.edit_message_text(
        f"<b>📋 Last log entries:</b>\n\n<pre>{tail}</pre>",
        parse_mode=ParseMode.HTML,
        reply_markup=back_home_keyboard(),
    )


async def handle_admin_broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    user = query.from_user

    if not _admin_check(user.id):
        await query.answer("Access denied.", show_alert=True)
        return

    context.user_data["awaiting_broadcast"] = True
    await query.edit_message_text(
        "📢 <b>Broadcast</b>\n\nSend the message you want to broadcast to all users.\n\nType /cancel to abort.",
        parse_mode=ParseMode.HTML,
        reply_markup=back_home_keyboard(),
    )


async def handle_broadcast_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Receive the broadcast text and send it to every user."""
    user = update.effective_user
    if not _admin_check(user.id):
        return
    if not context.user_data.get("awaiting_broadcast"):
        return

    context.user_data.pop("awaiting_broadcast", None)
    text = update.message.text

    if text and text.strip() == "/cancel":
        await update.message.reply_text("Broadcast cancelled.", reply_markup=back_home_keyboard())
        return

    users = await get_all_users()
    sent, failed = 0, 0
    for u in users:
        try:
            await context.bot.send_message(chat_id=u["user_id"], text=text)
            sent += 1
        except Exception:
            failed += 1

    await update.message.reply_text(
        f"📢 Broadcast complete.\n✅ Sent: {sent}\n❌ Failed: {failed}",
        reply_markup=back_home_keyboard(),
    )
    logger.info("Admin %s broadcast to %d users (%d failed)", user.id, sent, failed)
