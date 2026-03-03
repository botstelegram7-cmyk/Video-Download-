"""
╔══════════════════════════════════════════════════════════╗
║   ⋆｡° ✮   SERENA DOWNLOADER BOT   ✮ °｡⋆                ║
║   Owner   : @Xioqui_Xan                                 ║
║   Support : @TechnicalSerena                            ║
║   Bot     : @Universal_DownloadBot                      ║
╚══════════════════════════════════════════════════════════╝

Render-ready · Docker-compatible · Pyrogram 2.x
"""
import asyncio, sys, os, logging, datetime

# Add bot root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# ── 1. Web server first (Render needs PORT bound immediately) ─────────────────
from web.app import start as start_web
start_web()

# ── 2. Validate config ────────────────────────────────────────────────────────
from config import Config
try:
    Config.validate()
except EnvironmentError as e:
    print(f"[FATAL] {e}", flush=True)
    sys.exit(1)

# ── 3. Import shared client + plugins (registers @app.on_message handlers) ───
from client import app
import plugins.start     # noqa — registers all start/help/plans handlers
import plugins.download  # noqa — registers download handlers
import plugins.admin     # noqa — registers admin handlers

# ── 4. Other imports ──────────────────────────────────────────────────────────
import database as db
from queue_manager import queue
from pyrogram import idle

log = logging.getLogger(__name__)

# ── Cookie resolver ───────────────────────────────────────────────────────────
def _resolve_cookie(env_var: str, default_path: str) -> str:
    """
    If env var contains raw Netscape cookie text → write to /tmp and return path.
    Otherwise return file path if it exists.
    """
    raw = os.environ.get(env_var, "")
    if raw and ("\t" in raw or "# Netscape" in raw):
        dest = f"/tmp/{env_var.lower()}.txt"
        with open(dest, "w") as f:
            f.write(raw.strip())
        log.info("Cookie %s → %s", env_var, dest)
        return dest
    return default_path if (default_path and os.path.exists(default_path)) else ""

Config.YT_COOKIE = _resolve_cookie("YT_COOKIES", Config.YT_COOKIE)
Config.IG_COOKIE = _resolve_cookie("INSTAGRAM_COOKIES", Config.IG_COOKIE)
Config.TB_COOKIE = _resolve_cookie("TERABOX_COOKIES",   Config.TB_COOKIE)

# ── Main ──────────────────────────────────────────────────────────────────────
async def main():
    # Init DB
    await db.init()

    # Start queue
    await queue.start()

    # ── KEY FIX: explicit start/stop (not `async with`) ──────────────────────
    # Using `async with app:` can silently drop decorator-registered handlers
    # in Pyrogram 2.x on some environments. Explicit start is reliable.
    await app.start()

    me = await app.get_me()
    Config.BOT_USERNAME = me.username
    log.info("✅ Bot started as @%s", me.username)

    # Notify log channel
    if Config.LOG_CHANNEL:
        try:
            await app.send_message(
                Config.LOG_CHANNEL,
                f"»»──── 🟢 Bot Online ────««\n\n"
                f"🤖 @{me.username}\n"
                f"🕐 {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            )
        except Exception as e:
            log.warning("Log channel: %s", e)

    print("""
╔══════════════════════════════════════════════════╗
║  ✅  BOT IS ONLINE & RUNNING                     ║
║  ⋆｡° ✮   SERENA DOWNLOADER BOT   ✮ °｡⋆         ║
║  Owner   : @Xioqui_Xan                          ║
║  Support : @TechnicalSerena                     ║
╚══════════════════════════════════════════════════╝
""", flush=True)

    await idle()

    await app.stop()
    await queue.stop()
    log.info("Bot stopped.")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("[INFO] Stopped by user.", flush=True)
    except Exception as e:
        print(f"[FATAL] {e}", flush=True)
        log.critical("Fatal: %s", e, exc_info=True)
        sys.exit(1)
