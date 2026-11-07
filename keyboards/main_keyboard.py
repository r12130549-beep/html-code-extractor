"""
All inline keyboards for the bot.
"""
from telegram import InlineKeyboardButton, InlineKeyboardMarkup


def home_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🔗 Extract HTML", callback_data="menu_extract"),
            InlineKeyboardButton("📂 History",      callback_data="menu_history"),
        ],
        [
            InlineKeyboardButton("⚙️ Settings",    callback_data="menu_settings"),
            InlineKeyboardButton("❓ Help",         callback_data="menu_help"),
        ],
        [
            InlineKeyboardButton("👨‍💻 Developer",  callback_data="menu_developer"),
        ],
    ])


def extract_again_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🔄 Extract Again", callback_data="menu_extract"),
            InlineKeyboardButton("🏠 Home",           callback_data="menu_home"),
        ],
    ])


def back_home_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🏠 Back to Home", callback_data="menu_home")],
    ])


def history_keyboard(has_history: bool) -> InlineKeyboardMarkup:
    buttons = []
    if has_history:
        buttons.append([
            InlineKeyboardButton("🗑️ Clear History", callback_data="history_clear"),
        ])
    buttons.append([
        InlineKeyboardButton("🏠 Back to Home", callback_data="menu_home"),
    ])
    return InlineKeyboardMarkup(buttons)


def confirm_clear_history_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("✅ Yes, Clear",   callback_data="history_confirm_clear"),
            InlineKeyboardButton("❌ Cancel",        callback_data="menu_history"),
        ],
    ])


def settings_keyboard(s: dict) -> InlineKeyboardMarkup:
    """Build settings keyboard from current settings dict."""
    def tf(v: bool) -> str:
        return "✅" if v else "❌"

    return InlineKeyboardMarkup([
        [InlineKeyboardButton(
            f"📄 Filename: {s['output_filename']}", callback_data="setting_filename"
        )],
        [InlineKeyboardButton(
            f"🔡 Encoding: {s['encoding']}", callback_data="setting_encoding"
        )],
        [
            InlineKeyboardButton(
                f"📋 Headers: {tf(s['include_headers'])}", callback_data="setting_headers"
            ),
            InlineKeyboardButton(
                f"✨ Beautify: {tf(s['beautify_html'])}", callback_data="setting_beautify"
            ),
        ],
        [
            InlineKeyboardButton(
                f"🗑️ Auto-delete: {tf(s['auto_delete'])}", callback_data="setting_autodelete"
            ),
            InlineKeyboardButton(
                f"⏱️ Timeout: {s['timeout']}s", callback_data="setting_timeout"
            ),
        ],
        [InlineKeyboardButton("↩️ Reset to Defaults", callback_data="setting_reset")],
        [InlineKeyboardButton("🏠 Back to Home",       callback_data="menu_home")],
    ])


def encoding_keyboard() -> InlineKeyboardMarkup:
    encodings = ["utf-8", "latin-1", "ascii", "utf-16"]
    rows = [[InlineKeyboardButton(e, callback_data=f"enc_{e}")] for e in encodings]
    rows.append([InlineKeyboardButton("❌ Cancel", callback_data="menu_settings")])
    return InlineKeyboardMarkup(rows)


def timeout_keyboard() -> InlineKeyboardMarkup:
    options = [10, 20, 30, 60, 90, 120]
    rows = [
        [
            InlineKeyboardButton(f"{t}s", callback_data=f"timeout_{t}")
            for t in options[i:i+3]
        ]
        for i in range(0, len(options), 3)
    ]
    rows.append([InlineKeyboardButton("❌ Cancel", callback_data="menu_settings")])
    return InlineKeyboardMarkup(rows)


def admin_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("📊 Stats",         callback_data="admin_stats"),
            InlineKeyboardButton("👥 Users",          callback_data="admin_users"),
        ],
        [
            InlineKeyboardButton("📢 Broadcast",     callback_data="admin_broadcast"),
            InlineKeyboardButton("📋 Logs",           callback_data="admin_logs"),
        ],
        [InlineKeyboardButton("🏠 Back to Home",     callback_data="menu_home")],
    ])
