"""
╔═══════════════════════════════════════════════════╗
║   ⋆｡° ✮  SERENA DOWNLOADER BOT  ✮ °｡⋆           ║
║   -ˏˋ⋆  U L T I M A T E  D O W N L O A D E R    ║
║   Owner   :  @Xioqui_Xan                         ║
║   Support :  @TechnicalSerena                     ║
╚═══════════════════════════════════════════════════╝
"""
import asyncio, logging, datetime, os, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# ── Flask keep-alive thread (must be before asyncio.run) ─────────────────────
from web.app import start_flask_thread
start_flask_thread()

# ── Core imports ──────────────────────────────────────────────────────────────
from pyrogram import idle
from config import Config
from client import app
import database as db
from queue_manager import queue_manager

# ── Register handlers by importing plugins ────────────────────────────────────
# IMPORTANT: import BEFORE app.start() so decorators bind correctly
import plugins.start     # noqa
import plugins.download  # noqa
import plugins.admin     # noqa

logging.basicConfig(
    level   = logging.INFO,
    format  = "%(asctime)s │ %(name)-20s │ %(levelname)-8s │ %(message)s",
    handlers= [logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)

# ── Cookie helper ─────────────────────────────────────────────────────────────
def _resolve_cookie(env_key, default_path):
    raw = os.environ.get(env_key, "")
    if raw and ("\t" in raw or "# Netscape" in raw):
        os.makedirs("/tmp/cookies", exist_ok=True)
        dest = "/tmp/cookies/" + env_key.lower() + ".txt"
        with open(dest, "w") as f:
            f.write(raw.strip())
        logger.info("Cookie [%s] -> %s", env_key, dest)
        return dest
    if default_path and os.path.exists(default_path):
        return default_path
    return ""

Config.YT_COOKIES_PATH        = _resolve_cookie("YT_COOKIES",        Config.YT_COOKIES_PATH)
Config.INSTAGRAM_COOKIES_PATH = _resolve_cookie("INSTAGRAM_COOKIES", Config.INSTAGRAM_COOKIES_PATH)
Config.TERABOX_COOKIES_PATH   = _resolve_cookie("TERABOX_COOKIES",   Config.TERABOX_COOKIES_PATH)

# ── Main ──────────────────────────────────────────────────────────────────────
async def main():
    if not Config.validate():
        logger.error("❌ Invalid config — check BOT_TOKEN / API_ID / API_HASH")
        sys.exit(1)

    # Init DB
    try:
        await db.init_db()
        print("[DB] ✅ Database ready:", Config.DATABASE_PATH, flush=True)
    except Exception as e:
        print("[DB] ❌ Database init failed:", e, flush=True)
        sys.exit(1)

    # Start queue
    await queue_manager.start()
    print("[QUEUE] ✅ Queue manager ready", flush=True)

    # ── KEY FIX: Use explicit start/stop instead of `async with app:` ─────────
    # `async with app:` can miss decorator-registered handlers in Pyrogram 2.x
    await app.start()
    me = await app.get_me()
    Config.BOT_USERNAME = me.username
    print(f"[BOT] ✅ Logged in as @{me.username}", flush=True)

    # Notify log channel
    if Config.LOG_CHANNEL:
        try:
            await app.send_message(
                Config.LOG_CHANNEL,
                "»»──── 🤖 Bot Started ────««\n\n"
                "@" + me.username + " is **online**!\n"
                "🕐 " + datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            )
        except Exception as e:
            logger.warning("Log channel notify failed: %s", e)

    print("""
╔══════════════════════════════════════════╗
║   ✅  BOT IS NOW ONLINE & RUNNING!       ║
║   ⋆｡° ✮  SERENA DOWNLOADER  ✮ °｡⋆      ║
║   Owner   : @Xioqui_Xan                 ║
║   Support : @TechnicalSerena            ║
╚══════════════════════════════════════════╝
    """, flush=True)

    await idle()

    # Graceful shutdown
    await app.stop()
    await queue_manager.stop()
    print("[BOT] Stopped.", flush=True)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("[BOT] Stopped by user.", flush=True)
    except Exception as e:
        print(f"[BOT] FATAL: {e}", flush=True)
        logger.critical("Fatal: %s", e, exc_info=True)
        sys.exit(1)
