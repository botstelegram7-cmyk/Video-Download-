import os
from dotenv import load_dotenv
load_dotenv()

BOT_TOKEN         = os.environ.get("BOT_TOKEN", "")
API_ID            = int(os.environ.get("API_ID", "0"))
API_HASH          = os.environ.get("API_HASH", "")

OWNER_IDS         = [int(i) for i in os.getenv("OWNER_IDS", "1598576202").split(",") if i.strip()]
OWNER_USERNAME    = os.getenv("OWNER_USERNAME", "Xioqui_Xan")
SUPPORT_USERNAME  = os.getenv("SUPPORT_USERNAME", "TechnicalSerena")

FSUB_LINK         = os.getenv("FSUB_LINK", "https://t.me/TechnicalSerena")
FSUB_ID           = os.getenv("FSUB_ID", "")
LOG_CHANNEL       = os.getenv("LOG_CHANNEL", "")
START_PIC         = os.getenv("START_PIC", "")

FREE_LIMIT        = int(os.getenv("FREE_LIMIT",    "3"))
BASIC_LIMIT       = int(os.getenv("BASIC_LIMIT",   "15"))
PREMIUM_LIMIT     = int(os.getenv("PREMIUM_LIMIT", "50"))

DB_PATH           = os.getenv("DB_PATH", "/tmp/serena_db/bot.db")
DL_DIR            = os.getenv("DL_DIR",  "/tmp/serena_dl")
PORT              = int(os.getenv("PORT", "10000"))

YT_COOKIES        = os.getenv("YT_COOKIES",        "")
INSTAGRAM_COOKIES = os.getenv("INSTAGRAM_COOKIES", "")
TERABOX_COOKIES   = os.getenv("TERABOX_COOKIES",   "")

MAX_SIZE          = 2 * 1024 * 1024 * 1024   # 2 GB
