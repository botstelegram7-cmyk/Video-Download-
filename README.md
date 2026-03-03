# ⋆｡° ✮ SERENA DOWNLOADER BOT ✮ °｡⋆

> **Universal Telegram Video Downloader Bot**
> Owner: @Xioqui_Xan | Support: @TechnicalSerena

---

## 🚀 Features
- 🎥 YouTube (Video / Shorts / Playlist)
- 📸 Instagram (Reels / Posts / Stories)
- 🎵 TikTok / Twitter-X / Facebook
- 📦 Terabox
- 🌊 M3U8 / HLS Streams
- 🔗 Any direct download link
- 📄 .txt files with multiple links
- 🌐 1000+ sites via yt-dlp
- 🎵 Audio-only download mode
- ℹ️  URL info without downloading
- 📋 Download history
- 👑 Admin panel + user management
- 💎 Premium plan system
- ⏱  Real-time progress bars

## ⌨️ Commands

| Command | Description |
|---------|-------------|
| /start | Welcome & main menu |
| /help | Full help menu |
| /audio `<url>` | Download audio only |
| /info `<url>` | Get URL info |
| /history | Download history |
| /mystats | Your stats & quota |
| /queue | Active downloads |
| /cancel | Cancel downloads |
| /status | Bot status |
| /plans | View plans |
| /buy | Buy premium |
| /ping | Ping the bot |
| /feedback | Send feedback |

### 👑 Admin Commands
| Command | Description |
|---------|-------------|
| /givepremium `<id>` `<plan>` | Give plan to user |
| /removepremium `<id>` | Remove plan |
| /ban `<id>` | Ban user |
| /unban `<id>` | Unban user |
| /broadcast `<msg>` | Broadcast to all users |
| /stats | Bot statistics |
| /users | List premium users |
| /banned | List banned users |
| /restart | Restart bot |

## ⚙️ Setup

1. Copy `.env.example` to `.env`
2. Fill in `BOT_TOKEN`, `API_ID`, `API_HASH`
3. Set your `OWNER_IDS`
4. Run: `python bot.py`

## 🐳 Docker
```bash
docker build -t serena-dl-bot .
docker run --env-file .env serena-dl-bot
```

## 📦 Deploy on Render
1. Connect your GitHub repo
2. Set environment variables from `.env.example`
3. Start command: `python bot.py`
