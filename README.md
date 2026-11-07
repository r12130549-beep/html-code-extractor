# 🌐 HTML Extractor Pro Bot

A premium Telegram bot that downloads the complete HTML source of any webpage and sends it as a file.

---

## ✨ Features

- **HTML Extraction** — `/html <url>` downloads any webpage's HTML and sends it as a file
- **Animated Progress** — Real-time loading steps while extracting
- **Per-user Settings** — Filename, encoding, beautify, auto-delete, timeout
- **Extraction History** — View and clear your last 20 extractions
- **Admin Panel** — Stats, user list, broadcast messages, live log viewer
- **SSRF Protection** — Private/internal IPs blocked at DNS resolution
- **Secure** — SSL/HTTPS support, URL validation, non-root Docker container

---

## 🚀 Deployment

### Option 1 — Render.com (Recommended)

1. Push this folder to a GitHub repo.
2. Go to [render.com](https://render.com) → **New → Blueprint** → connect your repo.
   Render will auto-detect `render.yaml` and create a **Background Worker**.
3. In the Render dashboard → **Environment** → add secret:
   ```
   TELEGRAM_BOT_TOKEN = <your token from @BotFather>
   ADMIN_IDS          = <your Telegram user ID>   # optional
   ```
4. Click **Deploy**. The bot starts automatically.

> **Note:** Render free-tier workers spin down after inactivity.
> Use a paid plan (Starter $7/mo) or a cron ping to keep it alive.

---

### Option 2 — Docker (any VPS / local)

```bash
# Clone / copy the project
cd html_extractor_bot

# Create a .env file
cp .env.example .env          # then edit .env with your token
# — OR — export variables directly:
export TELEGRAM_BOT_TOKEN="your_token_here"
export ADMIN_IDS="123456789"   # optional

# Build and run
docker compose up -d

# View live logs
docker compose logs -f
```

**Stop the bot:**
```bash
docker compose down
```

---

### Option 3 — Plain Python (no Docker)

```bash
cd html_extractor_bot
pip install -r requirements.txt
export TELEGRAM_BOT_TOKEN="your_token_here"
python bot.py
```

---

## ⚙️ Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `TELEGRAM_BOT_TOKEN` | ✅ | Bot token from [@BotFather](https://t.me/BotFather) |
| `ADMIN_IDS` | optional | Comma-separated Telegram user IDs, e.g. `123,456` |

---

## 🤖 Bot Commands

| Command | Description |
|---------|-------------|
| `/start` | Open the home menu |
| `/html <url>` | Extract HTML from a URL |
| `/history` | View your extraction history |
| `/settings` | Configure your preferences |
| `/admin` | Admin panel (admins only) |
| `/help` | Help guide |

---

## 📁 Project Structure

```
html_extractor_bot/
├── Dockerfile              ← Multi-stage Docker build
├── docker-compose.yml      ← Local Docker orchestration
├── render.yaml             ← Render.com Blueprint config
├── requirements.txt
├── bot.py                  ← Entry point
├── config.py               ← Configuration & paths
├── handlers/
│   ├── start.py            ← /start, /help
│   ├── html_extractor.py   ← /html (core feature)
│   ├── history.py          ← /history
│   ├── settings.py         ← /settings
│   ├── admin.py            ← /admin
│   └── callbacks.py        ← Inline keyboard router
├── keyboards/
│   └── main_keyboard.py    ← All InlineKeyboardMarkup builders
├── services/
│   └── extractor.py        ← Async aiohttp + SSRF guard
├── utils/
│   ├── validators.py       ← URL validation
│   ├── helpers.py          ← Formatting utilities
│   └── logger.py           ← Rotating file logger
├── database/
│   └── db.py               ← aiosqlite data layer
├── logs/                   ← Rotating log files (volume-mounted)
├── temp/                   ← Temporary working files
└── extract/                ← Generated HTML files
```

---

## 🛡️ Admin Setup

1. Find your Telegram user ID — send `/start` to [@userinfobot](https://t.me/userinfobot).
2. Set `ADMIN_IDS=<your_id>` in your environment or Render dashboard.
3. Restart the bot and use `/admin`.

---

## 📦 Docker Notes

- **Multi-stage build** — compiler tools stay out of the final image (smaller, safer).
- **Non-root user** — container runs as `botuser` (UID 1000).
- **Volumes** — `logs/`, `database/`, and `extract/` are mounted as named volumes so data persists across container restarts.
- **No exposed port** — this is a polling-based background worker, not a web server.
