"""
╔══════════════════════════════════════════════════════════╗
║        ⚙️  SERENA DOWNLOADER BOT — CONFIG                ║
║   Owner   : @Xioqui_Xan    Support : @TechnicalSerena   ║
╚══════════════════════════════════════════════════════════╝
"""
import os, logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(name)-18s | %(levelname)-8s | %(message)s",
    handlers=[logging.StreamHandler()],
)

class Config:

    # ── 🔑 Required Credentials ─────────────────────────────
    BOT_TOKEN  = os.environ.get("BOT_TOKEN",  "")
    API_ID     = int(os.environ.get("API_ID",  0))
    API_HASH   = os.environ.get("API_HASH",   "")

    # ── 👑 Owner / Branding ─────────────────────────────────
    OWNER_IDS   = [int(x) for x in os.environ.get("OWNER_IDS", "1598576202").split(",") if x.strip()]
    OWNER_UNAME = os.environ.get("OWNER_USERNAME",  "Xioqui_Xan")       # no @
    SUPPORT_UNAME = os.environ.get("SUPPORT_USERNAME", "TechnicalSerena") # no @
    BOT_NAME    = "𝗦𝗲𝗿𝗲𝗻𝗮 𝗗𝗼𝘄𝗻𝗹𝗼𝗮𝗱𝗲𝗿 𝗕𝗼𝘁"

    # ── 📢 Channel ──────────────────────────────────────────
    FSUB_LINK   = os.environ.get("FSUB_LINK", "https://t.me/TechnicalSerena")
    FSUB_ID     = os.environ.get("FSUB_ID",   "")   # @channel or -100xxx; empty = disabled
    LOG_CHANNEL = os.environ.get("LOG_CHANNEL","")  # optional

    # ── 🖼️  Branding ─────────────────────────────────────────
    START_PIC   = os.environ.get("START_PIC",  "")  # URL of welcome photo/gif

    # ── 📊 Limits ────────────────────────────────────────────
    FREE_LIMIT    = int(os.environ.get("FREE_LIMIT",    "3"))
    BASIC_LIMIT   = int(os.environ.get("BASIC_LIMIT",  "15"))
    PREMIUM_LIMIT = int(os.environ.get("PREMIUM_LIMIT","50"))
    OWNER_LIMIT   = 999_999

    BASIC_DAYS   = 30
    PREMIUM_DAYS = 365

    # ── ⚙️  Download ─────────────────────────────────────────
    DL_DIR      = os.environ.get("DL_DIR",   "/tmp/serena_dl")
    MAX_SIZE    = int(os.environ.get("MAX_SIZE", str(2 * 1024**3)))   # 2 GB
    DL_TIMEOUT  = int(os.environ.get("DL_TIMEOUT", "3600"))
    QUEUE_SIZE  = int(os.environ.get("QUEUE_SIZE", "100"))
    PROGRESS_IV = 3   # seconds between progress edits

    # ── 💾 Database ──────────────────────────────────────────
    DB_PATH     = os.environ.get("DB_PATH", "/tmp/serena_db/bot.db")

    # ── 🍪 Cookies ───────────────────────────────────────────
    YT_COOKIE   = os.environ.get("YT_COOKIES_PATH",        "/app/cookies/youtube.txt")
    IG_COOKIE   = os.environ.get("INSTAGRAM_COOKIES_PATH", "/app/cookies/instagram.txt")
    TB_COOKIE   = os.environ.get("TERABOX_COOKIES_PATH",   "/app/cookies/terabox.txt")

    # ── 🌐 Web / Render ─────────────────────────────────────
    PORT        = int(os.environ.get("PORT", "10000"))  # Render default
    HOST        = "0.0.0.0"

    # ── Runtime (set by bot.py) ──────────────────────────────
    BOT_USERNAME = ""

    @classmethod
    def validate(cls):
        missing = []
        if not cls.BOT_TOKEN: missing.append("BOT_TOKEN")
        if not cls.API_ID:    missing.append("API_ID")
        if not cls.API_HASH:  missing.append("API_HASH")
        if missing:
            raise EnvironmentError(f"Missing required env vars: {', '.join(missing)}")

# Create dirs
os.makedirs(Config.DL_DIR,  exist_ok=True)
os.makedirs(os.path.dirname(Config.DB_PATH), exist_ok=True)
