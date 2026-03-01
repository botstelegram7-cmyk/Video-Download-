"""
╔══════════════════════════════════════════╗
║     ⚙️  B O T  C O N F I G U R A T I O N     ║
╚══════════════════════════════════════════╝
"""
import os
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s — %(name)s — %(levelname)s — %(message)s"
)
logger = logging.getLogger(__name__)

class Config:
    # ┌─────────────────────────────────────┐
    # │        🤖  BOT CREDENTIALS           │
    # └─────────────────────────────────────┘
    BOT_TOKEN     = os.environ.get("BOT_TOKEN", "")
    API_ID        = int(os.environ.get("API_ID", 0))
    API_HASH      = os.environ.get("API_HASH", "")

    # ┌─────────────────────────────────────┐
    # │        👑  OWNER CONFIG              │
    # └─────────────────────────────────────┘
    OWNER_IDS         = [int(x) for x in os.environ.get("OWNER_IDS", "1598576202").split(",") if x]
    OWNER_USERNAME    = os.environ.get("OWNER_USERNAME",  "@Xioqui_Xan")
    OWNER_USERNAME2   = os.environ.get("OWNER_USERNAME2", "@TechnicalSerena")

    # ┌─────────────────────────────────────┐
    # │        📢  CHANNELS                  │
    # └─────────────────────────────────────┘
    FORCE_SUB_CHANNEL    = os.environ.get("FORCE_SUB_CHANNEL",    "https://t.me/serenaunzipbot")
    FORCE_SUB_CHANNEL_ID = os.environ.get("FORCE_SUB_CHANNEL_ID", "@serenaunzipbot")
    LOG_CHANNEL          = os.environ.get("LOG_CHANNEL",          "")   # optional

    # ┌─────────────────────────────────────┐
    # │        🍪  COOKIES PATHS             │
    # └─────────────────────────────────────┘
    YT_COOKIES_PATH        = os.environ.get("YT_COOKIES_PATH",        "/app/cookies/youtube.txt")
    INSTAGRAM_COOKIES_PATH = os.environ.get("INSTAGRAM_COOKIES_PATH", "/app/cookies/instagram.txt")
    TERABOX_COOKIES_PATH   = os.environ.get("TERABOX_COOKIES_PATH",   "/app/cookies/terabox.txt")

    # ┌─────────────────────────────────────┐
    # │        🖼️  MEDIA / BRANDING          │
    # └─────────────────────────────────────┘
    START_PIC = os.environ.get("START_PIC", "")   # optional photo/gif URL

    # ┌─────────────────────────────────────┐
    # │        📊  PLANS & LIMITS            │
    # └─────────────────────────────────────┘
    BASIC_DAILY_LIMIT   = int(os.environ.get("BASIC_DAILY_LIMIT",   "3"))
    PREMIUM_DAILY_LIMIT = int(os.environ.get("PREMIUM_DAILY_LIMIT", "50"))
    OWNER_DAILY_LIMIT   = 999_999

    BASIC_PLAN_DAYS   = 30    # 1 month
    PREMIUM_PLAN_DAYS = 365   # 1 year

    # ┌─────────────────────────────────────┐
    # │        ⚙️  DOWNLOAD SETTINGS         │
    # └─────────────────────────────────────┘
    DOWNLOAD_DIR     = os.environ.get("DOWNLOAD_DIR",  "/tmp/downloads")
    MAX_FILE_SIZE    = int(os.environ.get("MAX_FILE_SIZE", str(2 * 1024 * 1024 * 1024)))  # 2 GB
    DOWNLOAD_TIMEOUT = int(os.environ.get("DOWNLOAD_TIMEOUT", "3600"))
    MAX_QUEUE_SIZE   = int(os.environ.get("MAX_QUEUE_SIZE",   "100"))
    PROGRESS_UPDATE_INTERVAL = 3   # seconds between progress updates

    # ┌─────────────────────────────────────┐
    # │        🌐  FLASK WEB SERVER          │
    # └─────────────────────────────────────┘
    PORT       = int(os.environ.get("PORT", "8080"))
    HOST       = os.environ.get("HOST", "0.0.0.0")
    SECRET_KEY = os.environ.get("SECRET_KEY", "advanced_dl_bot_secret")

    # ┌─────────────────────────────────────┐
    # │        💾  DATABASE                  │
    # └─────────────────────────────────────┘
    DATABASE_PATH = os.environ.get("DATABASE_PATH", "/app/data/bot.db")

    # ┌─────────────────────────────────────┐
    # │        🎨  AESTHETIC THEME           │
    # └─────────────────────────────────────┘
    DIVIDER     = "»»────────── ✦ ──────────««"
    DIVIDER_SM  = "──────────────────────"
    STAR_LINE   = "⋆｡° ✮ °｡⋆"
    BOT_NAME    = "𝗦𝗲𝗿𝗲𝗻𝗮 𝗗𝗼𝘄𝗻𝗹𝗼𝗮𝗱𝗲𝗿 𝗕𝗼𝘁"

    @classmethod
    def validate(cls):
        errors = []
        if not cls.BOT_TOKEN:   errors.append("BOT_TOKEN is missing")
        if not cls.API_ID:      errors.append("API_ID is missing")
        if not cls.API_HASH:    errors.append("API_HASH is missing")
        if errors:
            for e in errors: logger.error(f"Config Error: {e}")
            return False
        return True

os.makedirs(Config.DOWNLOAD_DIR, exist_ok=True)
os.makedirs(os.path.dirname(Config.DATABASE_PATH), exist_ok=True)
