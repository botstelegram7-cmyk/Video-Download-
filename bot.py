"""
╔═══════════════════════════════════════════════════╗
║   ⋆｡° ✮  SERENA DOWNLOADER BOT  ✮ °｡⋆           ║
║   Owner: @Xioqui_Xan  |  Support: @TechnicalSerena║
╚═══════════════════════════════════════════════════╝
"""
import asyncio, logging, datetime, os, sys

# ── Flask BEFORE asyncio.run() — avoids event loop conflict ──────────────────
from web.app import start_flask_thread
start_flask_thread()

from pyrogram import idle
from config import Config
from client import app
import database as db
from queue_manager import queue_manager
import handlers  # noqa — registers all @app.on_message decorators

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s │ %(name)-20s │ %(levelname)-8s │ %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)

# ── Cookie helper: paste Netscape text in Render env vars ────────────────────
def _resolve_cookie(env_key: str, default_path: str) -> str:
    raw = os.environ.get(env_key, "")
    if raw and ("\t" in raw or "# Netscape" in raw):
        os.makedirs("/tmp/cookies", exist_ok=True)
        dest = f"/tmp/cookies/{env_key.lower()}.txt"
        with open(dest, "w") as f:
            f.write(raw.strip())
        logger.info(f"✅ Cookie [{env_key}] → {dest}")
        return dest
    if default_path and os.path.exists(default_path):
        return default_path
    return ""

Config.YT_COOKIES_PATH        = _resolve_cookie("YT_COOKIES",        Config.YT_COOKIES_PATH)
Config.INSTAGRAM_COOKIES_PATH = _resolve_cookie("INSTAGRAM_COOKIES", Config.INSTAGRAM_COOKIES_PATH)
Config.TERABOX_COOKIES_PATH   = _resolve_cookie("TERABOX_COOKIES",   Config.TERABOX_COOKIES_PATH)

# ── Main ─────────────────────────────────────────────────────────────────────
async def main():
    if not Config.validate():
        logger.error("❌ Invalid config — check BOT_TOKEN / API_ID / API_HASH")
        sys.exit(1)

    await db.init_db()
    logger.info("✅ Database ready")

    await queue_manager.start()
    logger.info("✅ Queue manager ready")

    async with app:
        me = await app.get_me()
        Config.BOT_USERNAME = me.username
        logger.info(f"✅ Logged in as @{me.username}")

        if Config.LOG_CHANNEL:
            try:
                await app.send_message(Config.LOG_CHANNEL,
                    f"🤖 @{me.username} is **online**!\n"
                    f"🕐 {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            except Exception as e:
                logger.warning(f"Log channel: {e}")

        print("""
╔══════════════════════════════════════════╗
║   ✅  BOT IS NOW ONLINE & RUNNING!       ║
║   ⋆｡° ✮  SERENA DOWNLOADER  ✮ °｡⋆      ║
╚══════════════════════════════════════════╝
        """)
        await idle()

    await queue_manager.stop()
    logger.info("🛑 Stopped.")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Stopped by user.")
    except Exception as e:
        logger.critical(f"Fatal: {e}", exc_info=True)
        sys.exit(1)
