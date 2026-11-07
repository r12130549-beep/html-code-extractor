"""
Inline-keyboard callback router for all menu and settings buttons.
"""
from telegram import Update
from telegram.ext import ContextTypes
from telegram.constants import ParseMode

from config import BOT_NAME, BOT_VERSION, ADMIN_IDS
from database.db import (
    get_history, clear_history, get_settings, upsert_settings, upsert_user
)
from handlers.admin import (
    handle_admin_stats, handle_admin_users, handle_admin_logs, handle_admin_broadcast
)
from handlers.start import WELCOME_TEXT, HELP_TEXT, DEVELOPER_TEXT, ADMIN_NOTE
from keyboards.main_keyboard import (
    home_keyboard, history_keyboard, settings_keyboard,
    confirm_clear_history_keyboard, encoding_keyboard,
    timeout_keyboard, back_home_keyboard, admin_keyboard,
)
from utils.helpers import format_file_size, status_icon, truncate, bool_display
from utils.logger import logger


def _history_text(entries: list[dict]) -> str:
    if not entries:
        return (
            "╔══════════════════════════════╗\n"
            "║     📂  YOUR HISTORY         ║\n"
            "╚══════════════════════════════╝\n\n"
            "<i>No extractions yet.</i>\n\n"
            "Use <code>/html https://example.com</code> to get started!"
        )
    lines = [
        "╔══════════════════════════════╗",
        "║     📂  YOUR HISTORY         ║",
        "╚══════════════════════════════╝",
        "",
        f"Last <b>{len(entries)}</b> extractions:",
        "━━━━━━━━━━━━━━━━━━━━━━━━━━",
    ]
    for i, e in enumerate(entries, 1):
        icon = status_icon(e["status"])
        url_s = truncate(e["url"], 38)
        size_s = format_file_size(e["file_size"]) if e["file_size"] else "—"
        dt_s = e["created_at"][:16].replace("T", " ")
        lines += [
            f"<b>{i}.</b> {icon} <code>{url_s}</code>",
            f"    📄 {e['filename']}  |  💾 {size_s}  |  🕒 {dt_s}",
        ]
        if i < len(entries):
            lines.append("─────────────────────────────")
    return "\n".join(lines)


def _settings_text(s: dict) -> str:
    return (
        "╔══════════════════════════════════╗\n"
        "║       ⚙️  YOUR SETTINGS          ║\n"
        "╚══════════════════════════════════╝\n\n"
        f"📄 <b>Output Filename:</b>  <code>{s['output_filename']}</code>\n"
        f"🔡 <b>Encoding:</b>          <code>{s['encoding']}</code>\n"
        f"📋 <b>Include Headers:</b>   {bool_display(s['include_headers'])}\n"
        f"✨ <b>Beautify HTML:</b>     {bool_display(s['beautify_html'])}\n"
        f"🗑️ <b>Auto-delete temp:</b>  {bool_display(s['auto_delete'])}\n"
        f"⏱️ <b>Timeout:</b>           {s['timeout']}s\n\n"
        "<i>Tap a setting to change it.</i>"
    )


async def callback_router(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    user = query.from_user
    data = query.data

    # ── Admin sub-routes ────────────────────────────────────────────────────
    if data == "admin_stats":
        return await handle_admin_stats(update, context)
    if data == "admin_users":
        return await handle_admin_users(update, context)
    if data == "admin_logs":
        return await handle_admin_logs(update, context)
    if data == "admin_broadcast":
        return await handle_admin_broadcast(update, context)

    # ── Home ────────────────────────────────────────────────────────────────
    if data == "menu_home":
        text = WELCOME_TEXT.format(
            bot_name=BOT_NAME,
            version=BOT_VERSION,
            first_name=user.first_name,
        )
        if user.id in ADMIN_IDS:
            text += ADMIN_NOTE
        await query.edit_message_text(
            text, parse_mode=ParseMode.HTML, reply_markup=home_keyboard()
        )

    # ── Extract ─────────────────────────────────────────────────────────────
    elif data == "menu_extract":
        await query.edit_message_text(
            "🔗 <b>HTML Extractor</b>\n\nSend a URL with the /html command:\n\n"
            "<code>/html https://example.com</code>",
            parse_mode=ParseMode.HTML,
            reply_markup=back_home_keyboard(),
        )

    # ── History ─────────────────────────────────────────────────────────────
    elif data == "menu_history":
        entries = await get_history(user.id)
        await query.edit_message_text(
            _history_text(entries),
            parse_mode=ParseMode.HTML,
            reply_markup=history_keyboard(bool(entries)),
        )

    elif data == "history_clear":
        await query.edit_message_text(
            "🗑️ <b>Clear History</b>\n\nAre you sure you want to delete all your extraction history?",
            parse_mode=ParseMode.HTML,
            reply_markup=confirm_clear_history_keyboard(),
        )

    elif data == "history_confirm_clear":
        count = await clear_history(user.id)
        logger.info("User %s cleared %d history entries", user.id, count)
        await query.edit_message_text(
            f"✅ Cleared <b>{count}</b> history entries.",
            parse_mode=ParseMode.HTML,
            reply_markup=back_home_keyboard(),
        )

    # ── Settings ─────────────────────────────────────────────────────────────
    elif data == "menu_settings":
        s = await get_settings(user.id)
        await query.edit_message_text(
            _settings_text(s),
            parse_mode=ParseMode.HTML,
            reply_markup=settings_keyboard(s),
        )

    elif data == "setting_headers":
        s = await get_settings(user.id)
        await upsert_settings(user.id, include_headers=not s["include_headers"])
        s = await get_settings(user.id)
        await query.edit_message_text(
            _settings_text(s), parse_mode=ParseMode.HTML, reply_markup=settings_keyboard(s)
        )

    elif data == "setting_beautify":
        s = await get_settings(user.id)
        await upsert_settings(user.id, beautify_html=not s["beautify_html"])
        s = await get_settings(user.id)
        await query.edit_message_text(
            _settings_text(s), parse_mode=ParseMode.HTML, reply_markup=settings_keyboard(s)
        )

    elif data == "setting_autodelete":
        s = await get_settings(user.id)
        await upsert_settings(user.id, auto_delete=not s["auto_delete"])
        s = await get_settings(user.id)
        await query.edit_message_text(
            _settings_text(s), parse_mode=ParseMode.HTML, reply_markup=settings_keyboard(s)
        )

    elif data == "setting_encoding":
        await query.edit_message_text(
            "🔡 <b>Select Encoding</b>\n\nChoose the character encoding for your HTML files:",
            parse_mode=ParseMode.HTML,
            reply_markup=encoding_keyboard(),
        )

    elif data.startswith("enc_"):
        enc = data[4:]
        await upsert_settings(user.id, encoding=enc)
        s = await get_settings(user.id)
        await query.edit_message_text(
            _settings_text(s), parse_mode=ParseMode.HTML, reply_markup=settings_keyboard(s)
        )

    elif data == "setting_timeout":
        await query.edit_message_text(
            "⏱️ <b>Select Timeout</b>\n\nChoose the maximum wait time per request:",
            parse_mode=ParseMode.HTML,
            reply_markup=timeout_keyboard(),
        )

    elif data.startswith("timeout_"):
        try:
            t = int(data[8:])
        except ValueError:
            await query.answer("Invalid timeout value.", show_alert=True)
            return
        await upsert_settings(user.id, timeout=t)
        s = await get_settings(user.id)
        await query.edit_message_text(
            _settings_text(s), parse_mode=ParseMode.HTML, reply_markup=settings_keyboard(s)
        )

    elif data == "setting_filename":
        context.user_data["awaiting_filename"] = True
        await query.edit_message_text(
            "📄 <b>Set Output Filename</b>\n\nReply with your preferred filename (must end in .html):\n"
            "Example: <code>mypage.html</code>",
            parse_mode=ParseMode.HTML,
            reply_markup=back_home_keyboard(),
        )

    elif data == "setting_reset":
        from config import DEFAULT_SETTINGS
        await upsert_settings(user.id, **DEFAULT_SETTINGS)
        s = await get_settings(user.id)
        await query.edit_message_text(
            "↩️ Settings reset to defaults.\n\n" + _settings_text(s),
            parse_mode=ParseMode.HTML,
            reply_markup=settings_keyboard(s),
        )

    # ── Help ─────────────────────────────────────────────────────────────────
    elif data == "menu_help":
        await query.edit_message_text(
            HELP_TEXT,
            parse_mode=ParseMode.HTML,
            reply_markup=back_home_keyboard(),
        )

    # ── Developer ─────────────────────────────────────────────────────────────
    elif data == "menu_developer":
        await query.edit_message_text(
            DEVELOPER_TEXT.format(bot_name=BOT_NAME, version=BOT_VERSION),
            parse_mode=ParseMode.HTML,
            reply_markup=back_home_keyboard(),
        )


async def handle_text_input(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle free-text messages for settings that require text input."""
    user = update.effective_user

    # Filename change
    if context.user_data.get("awaiting_filename"):
        context.user_data.pop("awaiting_filename")
        name = update.message.text.strip()
        if not name.endswith(".html"):
            name += ".html"
        # Sanitise
        name = "".join(c for c in name if c.isalnum() or c in ("-", "_", "."))
        if not name or name == ".html":
            name = "extract.html"
        await upsert_settings(user.id, output_filename=name)
        s = await get_settings(user.id)
        await update.message.reply_text(
            f"✅ Filename updated to <code>{name}</code>\n\n" + _settings_text(s),
            parse_mode=ParseMode.HTML,
            reply_markup=settings_keyboard(s),
        )
        return

    # Broadcast message relay (handled in admin.py via admin handler)
    from handlers.admin import handle_broadcast_message
    await handle_broadcast_message(update, context)
