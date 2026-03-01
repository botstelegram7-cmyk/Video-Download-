"""
╔═══════════════════════════════════════════════════╗
║                                                   ║
║   ⋆｡° ✮  SERENA DOWNLOADER BOT  ✮ °｡⋆           ║
║                                                   ║
║   -ˏˋ⋆  U L T I M A T E  D O W N L O A D E R    ║
║                    ⋆ˊˎ-                          ║
║                                                   ║
║   Owner   :  @Xioqui_Xan                         ║
║   Support :  @TechnicalSerena                     ║
║                                                   ║
╚═══════════════════════════════════════════════════╝
"""
import asyncio, logging, os, sys
from pyrogram import Client, idle           # ← idle() is the correct keep-alive
from config import Config
import database as db
from queue_manager import queue_manager
from web.app import start_flask_thread

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s │ %(name)-20s │ %(levelname)-8s │ %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)

# ═══════════════════════════════════════════════════
#  COOKIE HELPER — write env-string to temp file
#  Supports BOTH:
#    • Env var = file path  (e.g. /app/cookies/youtube.txt)
#    • Env var = raw Netscape cookie text (paste entire file content)
# ═══════════════════════════════════════════════════
def _resolve_cookie(env_key: str, default_path: str) -> str:
    raw = os.environ.get(env_key, "")
    # Pasted Netscape cookie string → write to temp file
    if raw and ("\t" in raw or "# Netscape" in raw):
        os.makedirs("/tmp/cookies", exist_ok=True)
        dest = f"/tmp/cookies/{env_key.lower().replace('_cookies','')}.txt"
        with open(dest, "w") as f:
            f.write(raw.strip())
        logger.info(f"✅ Cookie from env [{env_key}] → {dest}")
        return dest
    # It's a path string
    if default_path and os.path.exists(default_path):
        return default_path
    return ""

Config.YT_COOKIES_PATH        = _resolve_cookie("YT_COOKIES",        Config.YT_COOKIES_PATH)
Config.INSTAGRAM_COOKIES_PATH = _resolve_cookie("INSTAGRAM_COOKIES", Config.INSTAGRAM_COOKIES_PATH)
Config.TERABOX_COOKIES_PATH   = _resolve_cookie("TERABOX_COOKIES",   Config.TERABOX_COOKIES_PATH)

# ═══════════════════════════════════════════════════
#  CLIENT  ─  plugins= auto-loads all handlers in /plugins/
#  This is the CORRECT way in Pyrogram 2.x so that
#  @Client.on_message decorators properly bind to THIS instance.
# ═══════════════════════════════════════════════════
app = Client(
    name="SerenaDownloaderBot",
    api_id=Config.API_ID,
    api_hash=Config.API_HASH,
    bot_token=Config.BOT_TOKEN,
    workers=8,
    sleep_threshold=60,
    plugins=dict(root="plugins"),           # ← KEY FIX: auto-register all handlers
)

# ═══════════════════════════════════════════════════
#  STARTUP
# ═══════════════════════════════════════════════════
async def startup():
    logger.info("»»──── 🚀 Starting Bot ────««")

    await db.init_db()
    logger.info("✅ Database ready")

    await queue_manager.start()
    logger.info("✅ Queue manager ready")

    start_flask_thread()
    logger.info(f"✅ Flask web server on port {Config.PORT}")

    me = await app.get_me()
    Config.BOT_USERNAME = me.username
    logger.info(f"✅ Logged in as @{me.username}")

    if Config.LOG_CHANNEL:
        try:
            import datetime
            await app.send_message(
                Config.LOG_CHANNEL,
                f"»»──── 🤖 Bot Started ────««\n\n"
                f"🤖 @{me.username} is **online**!\n"
                f"🕐 {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            )
        except Exception as e:
            logger.warning(f"Log channel notify failed: {e}")

    print("""
╔══════════════════════════════════════════╗
║   ✅  BOT IS NOW ONLINE & RUNNING!       ║
║   ⋆｡° ✮  SERENA DOWNLOADER  ✮ °｡⋆      ║
╚══════════════════════════════════════════╝
    """)

# ═══════════════════════════════════════════════════
#  MAIN
# ═══════════════════════════════════════════════════
async def main():
    if not Config.validate():
        logger.error("❌ Invalid configuration! Check your environment variables.")
        sys.exit(1)

    await app.start()
    await startup()

    # ↓ idle() correctly suspends while Pyrogram processes updates
    # asyncio.Event().wait() was the BUG — it never yielded to Pyrogram workers
    await idle()

    await queue_manager.stop()
    await app.stop()
    logger.info("»»──── 🛑 Bot stopped gracefully ────««")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Stopped by user.")
    except Exception as e:
        logger.critical(f"Fatal: {e}", exc_info=True)
        sys.exit(1)
