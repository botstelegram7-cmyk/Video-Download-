# ⋆｡° ✮  SERENA DOWNLOADER BOT  ✮ °｡⋆
### »»────── 🌐 Universal Telegram Downloader Bot ──────««

> **⚠️ Render Deployment Disclaimer:**  
> This bot is designed to be deployed on [Render](https://render.com) as a **Docker Web Service**.  
> Render free tier **spins down** after inactivity — the built-in Flask server acts as a keep-alive endpoint.  
> For production, use **Render Paid** or add an external uptime monitor (e.g., [UptimeRobot](https://uptimerobot.com)) pinging your `/ping` endpoint.

---

## ✦ Features

| Feature | Description |
|---|---|
| 🎥 YouTube | Videos, Shorts, Music, Playlists |
| 📸 Instagram | Reels, Posts, Stories |
| 📦 Terabox | All Terabox variants |
| 🌊 M3U8 / HLS | Live streams & VOD |
| 🔗 Direct Links | Any MP4, PDF, ZIP, etc. |
| 📄 TXT File | Batch download from link list |
| 🌐 1000+ Sites | Via yt-dlp backend |
| 🎬 Telegram Playable | Auto re-mux to H.264/AAC |
| 🖼️ Thumbnails | Auto-extracted from video/PDF |
| 🏷️ Metadata | Title, Date, User, Bot tag |
| 📋 Queue System | Fair per-user download queue |
| 💎 Premium Plans | Free / Basic / Premium tiers |
| 🔔 Force Subscribe | Channel join requirement |
| 📡 Log Channel | All downloads forwarded |
| 📊 Progress Bars | Speed, ETA, %, aesthetic UI |
| 🐳 Docker Ready | One-command deploy |

---

## ✦ Commands

### 👤 User Commands
```
/start      — Welcome screen
/help       — Help & command list
/cancel     — Cancel your downloads
/mystats    — Your stats & plan info
/queue      — View your download queue
/status     — Bot uptime & stats
/plans      — View plans & pricing
/buy        — Purchase a plan
/settings   — Your settings
```

### 👑 Admin / Owner Commands
```
/givepremium <user_id> <plan>  — Grant plan (basic/premium)
/removepremium <user_id>       — Revoke plan
/ban <user_id>                 — Ban a user
/unban <user_id>               — Unban a user
/broadcast <message>           — Broadcast to all users
/stats                         — Bot statistics
/users                         — List premium users
```

---

## ✦ Plans

| Plan | Downloads/Day | Duration | Notes |
|---|---|---|---|
| 🆓 Free | 3/day | Unlimited | Basic access |
| 🥉 Basic | 3/day | 1 Month | Priority queue |
| 💎 Premium | 50/day | 1 Year | All features + VIP |
| 👑 Owner | Unlimited | Always | No restrictions |

**Payment:** Contact owners → Pay via UPI/QR → Send screenshot → Plan activated instantly!

---

## ✦ Deployment on Render

### Step 1 — Fork & Prepare
1. Fork this repo to your GitHub
2. Add your cookie files to `/cookies/` folder:
   - `cookies/youtube.txt`
   - `cookies/instagram.txt`  
   - `cookies/terabox.txt`
3. Push to GitHub

### Step 2 — Create Render Service
1. Go to [Render Dashboard](https://dashboard.render.com)
2. Click **New → Web Service**
3. Connect your GitHub repo
4. Set **Runtime** → **Docker**
5. Set **Region** → Choose closest to you

### Step 3 — Environment Variables
Add these in Render's **Environment** section:

| Variable | Value | Required |
|---|---|---|
| `BOT_TOKEN` | Your Telegram bot token | ✅ |
| `API_ID` | From my.telegram.org | ✅ |
| `API_HASH` | From my.telegram.org | ✅ |
| `OWNER_IDS` | Your Telegram user ID | ✅ |
| `FORCE_SUB_CHANNEL` | `https://t.me/your_channel` | ✅ |
| `FORCE_SUB_CHANNEL_ID` | `@your_channel` | ✅ |
| `LOG_CHANNEL` | `@log_channel` or `-100xxx` | Optional |
| `START_PIC` | URL to start image/gif | Optional |
| `OWNER_USERNAME` | `@Xioqui_Xan` | Optional |
| `OWNER_USERNAME2` | `@TechnicalSerena` | Optional |

### Step 4 — Deploy
1. Click **Create Web Service**
2. Wait for build to complete (3-5 minutes)
3. Bot will start automatically!

---

## ✦ Local Docker Deployment

```bash
# Clone
git clone <your-repo>
cd AdvancedDLBot

# Configure
cp .env.example .env
nano .env  # fill in your values

# Add cookies (optional but recommended)
# Place your cookie files in ./cookies/

# Build & Run
docker-compose up -d

# View logs
docker-compose logs -f
```

---

## ✦ Cookie Files

Cookie files allow downloading age-restricted, private, or login-required content.

### How to get cookies:
1. Install [Get cookies.txt LOCALLY](https://chrome.google.com/webstore/detail/get-cookiestxt-locally/) Chrome extension
2. Log in to YouTube / Instagram / Terabox
3. Export cookies in **Netscape format**
4. Save as `youtube.txt`, `instagram.txt`, `terabox.txt` in `/cookies/` folder

On Render: Upload cookies via **Render Disk** or use **environment variable** to pass cookie content.

---

## ✦ Architecture

```
AdvancedDLBot/
├── bot.py                  ← Main entry point
├── config.py               ← Configuration
├── database.py             ← SQLite with aiosqlite
├── queue_manager.py        ← Async download queue
├── handlers/
│   ├── start.py            ← /start, /help, callbacks
│   ├── download.py         ← Download & upload logic
│   └── admin.py            ← Admin commands
├── downloader/
│   ├── universal.py        ← yt-dlp + direct + m3u8
│   └── processor.py        ← ffmpeg, thumbnails, metadata
├── utils/
│   ├── progress.py         ← Aesthetic progress bars
│   ├── helpers.py          ← URL detection, utilities
│   └── decorators.py       ← Auth, limit, ban checks
├── web/
│   └── app.py              ← Flask health server
├── cookies/                ← Cookie files (gitignored)
├── Dockerfile
├── docker-compose.yml
└── requirements.txt
```

---

## ✦ Technology Stack

- **Pyrogram** — Telegram MTProto client
- **yt-dlp** — Universal media downloader
- **FFmpeg** — Video processing & streaming
- **aiohttp** — Async HTTP downloads
- **aiosqlite** — Async SQLite database
- **PyMuPDF** — PDF thumbnail extraction
- **Pillow** — Image processing
- **Flask** — Health check web server

---

## ✦ Support & Contact

| Contact | Link |
|---|---|
| 👑 Owner | [@Xioqui_Xan](https://t.me/Xioqui_Xan) |
| 📞 Support | [@TechnicalSerena](https://t.me/TechnicalSerena) |
| 🔔 Updates | [Join Channel](https://t.me/serenaunzipbot) |

---

> ⋆ ｡˚ ⋆  Made with ♡ by **@Xioqui_Xan** & **@TechnicalSerena**  ⋆ ˚｡ ⋆
