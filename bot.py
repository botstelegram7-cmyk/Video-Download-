"""
╔═══════════════════════════════════════════════════╗
║   ⋆｡° ✮  SERENA DOWNLOADER BOT  ✮ °｡⋆           ║
║   -ˏˋ⋆  U L T I M A T E  D O W N L O A D E R    ║
║   Owner   :  @Xioqui_Xan                         ║
║   Support :  @TechnicalSerena                     ║
╚═══════════════════════════════════════════════════╝
"""
import asyncio, logging, datetime, os, sys
from pyrogram import Client, idle
from config import Config
import database as db
from queue_manager import queue_manager

# ─── Flask must start BEFORE asyncio.run() ───────────────────────────────────
# Reason: starting a thread INSIDE asyncio.run() on Python 3.11 causes
# Pyrogram's dispatcher coroutines to bind to a "different loop", crashing
# with: RuntimeError: Future attached to a different loop
from web.app import start_flask_thread
start_flask_thread()          # ← outside any event loop, before asyncio.run()

# ─── Logging ─────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s │ %(name)-20s │ %(levelname)-8s │ %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)

# ─── Cookie helper ───────────────────────────────────────────────────────────
# On Render, add env vars with the FULL Netscape cookie text as value:
#   YT_COOKIES          → YouTube cookie text
#   INSTAGRAM_COOKIES   → Instagram cookie text
#   TERABOX_COOKIES     → Terabox cookie text
def _resolve_cookie(env_key: str, default_path: str) -> str:
    raw = os.environ.get(env_key, "")
    if raw and ("\t" in raw or "# Netscape" in raw):
        os.makedirs("/tmp/cookies", exist_ok=True)
        dest = f"/tmp/cookies/{env_key.lower()}.txt"
        with open(dest, "w") as f:
            f.write(raw.strip())
        logger.info(f"✅ Cookie [{env_key}] written → {dest}")
        return dest
    if default_path and os.path.exists(default_path):
        return default_path
    return ""

Config.YT_COOKIES_PATH        = _resolve_cookie("YT_COOKIES",        Config.YT_COOKIES_PATH)
Config.INSTAGRAM_COOKIES_PATH = _resolve_cookie("INSTAGRAM_COOKIES", Config.INSTAGRAM_COOKIES_PATH)
Config.TERABOX_COOKIES_PATH   = _resolve_cookie("TERABOX_COOKIES",   Config.TERABOX_COOKIES_PATH)

# ─── Pyrogram client ─────────────────────────────────────────────────────────
app = Client(
    name="SerenaDownloaderBot",
    api_id=Config.API_ID,
    api_hash=Config.API_HASH,
    bot_token=Config.BOT_TOKEN,
    workers=8,
    sleep_threshold=60,
    plugins=dict(root="plugins"),   # auto-loads all handlers in /plugins/
)

# ─── Main ────────────────────────────────────────────────────────────────────
async def main():
    if not Config.validate():
        logger.error("❌ Invalid config — check BOT_TOKEN / API_ID / API_HASH")
        sys.exit(1)

    await db.init_db()
    logger.info("✅ Database ready")

    await queue_manager.start()
    logger.info("✅ Queue manager ready")

    # async with handles start() + stop() on the SAME event loop (no loop conflict)
    async with app:
        me = await app.get_me()
        Config.BOT_USERNAME = me.username
        logger.info(f"✅ Logged in as @{me.username}")

        if Config.LOG_CHANNEL:
            try:
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

        await idle()    # Pyrogram workers run freely here

    await queue_manager.stop()
    logger.info("»»──── 🛑 Stopped gracefully ────««")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Stopped by user.")
    except Exception as e:
        logger.critical(f"Fatal: {e}", exc_info=True)
        sys.exit(1)
