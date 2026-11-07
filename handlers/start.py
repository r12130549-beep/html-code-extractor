"""
/start command handler — shows the premium home menu.
"""
from telegram import Update
from telegram.ext import ContextTypes
from telegram.constants import ParseMode

from config import BOT_NAME, BOT_VERSION, ADMIN_IDS
from database.db import upsert_user
from keyboards.main_keyboard import home_keyboard, admin_keyboard
from utils.logger import logger


WELCOME_TEXT = """
╔══════════════════════════════════╗
║   🌐  {bot_name}  🌐   ║
║         v{version}              ║
╚══════════════════════════════════╝

👋 Welcome, <b>{first_name}</b>!

I extract the complete HTML source of any webpage \
and send it to you as a ready-to-use file.

━━━━━━━━━━━━━━━━━━━━━━━━━━
⚡ <b>Quick Extract</b>
Just type:  <code>/html https://example.com</code>

━━━━━━━━━━━━━━━━━━━━━━━━━━
🔒 <i>Secure  ·  Fast  ·  Private</i>
""".strip()

ADMIN_NOTE = "\n\n🛡️ <b>Admin panel available</b> — use /admin"

HELP_TEXT = """
╔══════════════════════════════╗
║        ❓  HELP GUIDE        ║
╚══════════════════════════════╝

<b>Commands</b>
/start  — Open the home menu
/html   — Extract HTML from a URL
/history — View your extraction history
/settings — Configure your preferences
/admin  — Admin panel (admins only)
/help   — Show this message

<b>Usage</b>
<code>/html https://example.com</code>

<b>What I do</b>
① Validate your URL
② Connect securely to the website
③ Download the complete HTML source
④ Package it as <code>extract.html</code>
⑤ Send the file straight to you

<b>Settings you can configure</b>
• Output filename
• Character encoding (UTF-8, Latin-1…)
• Include HTTP response headers
• Beautify / pretty-print HTML
• Auto-delete temp files
• Request timeout

━━━━━━━━━━━━━━━━━━━━━━━━━━
💡 <i>Tip: Use /settings to personalise your experience</i>
""".strip()

DEVELOPER_TEXT = """
╔══════════════════════════════╗
║     👨‍💻  DEVELOPER INFO      ║
╚══════════════════════════════╝

🤖 <b>Bot:</b> {bot_name} v{version}

⚙️ <b>Technology Stack</b>
• Python 3.11+  (async / await)
• python-telegram-bot v20
• aiohttp  —  async HTTP client
• aiosqlite  —  async SQLite
• BeautifulSoup4  —  HTML parsing

📦 <b>Features</b>
✅ URL validation &amp; sanitisation
✅ Async multi-user architecture
✅ Per-user history &amp; settings
✅ Admin panel &amp; broadcast
✅ Rotating log files
✅ Graceful error handling
✅ SSL / HTTPS support
✅ HTML beautifier (optional)

━━━━━━━━━━━━━━━━━━━━━━━━━━
🔒 <i>Open-source · Secure · Maintained</i>
""".strip()


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    await upsert_user(user.id, user.username, user.first_name)
    logger.info("User %s started the bot", user.id)

    text = WELCOME_TEXT.format(
        bot_name=BOT_NAME,
        version=BOT_VERSION,
        first_name=user.first_name,
    )
    if user.id in ADMIN_IDS:
        text += ADMIN_NOTE

    await update.message.reply_text(
        text,
        parse_mode=ParseMode.HTML,
        reply_markup=home_keyboard(),
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        HELP_TEXT,
        parse_mode=ParseMode.HTML,
        reply_markup=__import__("keyboards.main_keyboard", fromlist=["back_home_keyboard"]).back_home_keyboard(),
    )
