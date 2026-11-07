"""
/settings command handler — per-user configuration.
"""
from telegram import Update
from telegram.ext import ContextTypes
from telegram.constants import ParseMode

from database.db import get_settings, upsert_settings, upsert_user
from keyboards.main_keyboard import settings_keyboard
from utils.helpers import bool_display
from utils.logger import logger


def _settings_text(s: dict) -> str:
    return f"""
╔══════════════════════════════════╗
║       ⚙️  YOUR SETTINGS          ║
╚══════════════════════════════════╝

📄 <b>Output Filename:</b>  <code>{s['output_filename']}</code>
🔡 <b>Encoding:</b>          <code>{s['encoding']}</code>
📋 <b>Include Headers:</b>   {bool_display(s['include_headers'])}
✨ <b>Beautify HTML:</b>     {bool_display(s['beautify_html'])}
🗑️ <b>Auto-delete temp:</b>  {bool_display(s['auto_delete'])}
⏱️ <b>Timeout:</b>           {s['timeout']}s

<i>Tap a setting to change it.</i>
""".strip()


async def settings_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    await upsert_user(user.id, user.username, user.first_name)
    s = await get_settings(user.id)
    logger.info("User %s opened settings", user.id)
    await update.message.reply_text(
        _settings_text(s),
        parse_mode=ParseMode.HTML,
        reply_markup=settings_keyboard(s),
    )
