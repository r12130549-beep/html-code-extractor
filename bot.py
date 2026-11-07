"""
Entry point for HTML Extractor Bot.
"""
import sys
import asyncio

from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
)

from config import BOT_TOKEN, BOT_NAME
from database.db import init_db
from handlers.start import start_command, help_command
from handlers.html_extractor import html_command
from handlers.history import history_command
from handlers.settings import settings_command
from handlers.admin import admin_command
from handlers.callbacks import callback_router, handle_text_input
from utils.logger import logger


def build_application() -> Application:
    if not BOT_TOKEN:
        logger.error("TELEGRAM_BOT_TOKEN is not set. Aborting.")
        sys.exit(1)

    app = Application.builder().token(BOT_TOKEN).build()

    # ── Command handlers ────────────────────────────────────────────────────
    app.add_handler(CommandHandler("start",    start_command))
    app.add_handler(CommandHandler("help",     help_command))
    app.add_handler(CommandHandler("html",     html_command))
    app.add_handler(CommandHandler("history",  history_command))
    app.add_handler(CommandHandler("settings", settings_command))
    app.add_handler(CommandHandler("admin",    admin_command))

    # ── Inline keyboard callbacks ───────────────────────────────────────────
    app.add_handler(CallbackQueryHandler(callback_router))

    # ── Free-text messages (settings input, broadcast text) ─────────────────
    app.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_input)
    )

    return app


async def main() -> None:
    await init_db()
    logger.info("Database initialised.")

    app = build_application()
    logger.info("%s is starting…", BOT_NAME)

    await app.initialize()
    await app.start()
    await app.updater.start_polling(drop_pending_updates=True)

    logger.info("%s is running. Press Ctrl+C to stop.", BOT_NAME)

    # Keep alive until interrupted
    stop_event = asyncio.Event()
    try:
        await stop_event.wait()
    except (KeyboardInterrupt, SystemExit):
        pass
    finally:
        logger.info("Shutting down %s…", BOT_NAME)
        await app.updater.stop()
        await app.stop()
        await app.shutdown()


if __name__ == "__main__":
    asyncio.run(main())
