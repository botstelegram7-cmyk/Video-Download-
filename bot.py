"""
╔══════════════════════════════════════════════════════════╗
║   ⋆｡° ✮   SERENA DOWNLOADER BOT   ✮ °｡⋆                ║
║   Owner   : @Xioqui_Xan                                 ║
║   Support : @TechnicalSerena                            ║
╚══════════════════════════════════════════════════════════╝
"""
import asyncio, sys, os, logging, datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# ── 1. Web server first (Render needs PORT bound fast) ────────────────────────
from web.app import start as start_web
start_web()

# ── 2. Config & validation ────────────────────────────────────────────────────
from config import Config
try:
    Config.validate()
except EnvironmentError as e:
    print(f"[FATAL] {e}", flush=True)
    sys.exit(1)

# ══════════════════════════════════════════════════════
#  COOKIE RESOLVER
#  Render env vars can contain raw Netscape cookie text.
#  We detect this and write to /tmp so yt-dlp can read it.
# ══════════════════════════════════════════════════════
def _write_cookie(env_var: str, default_path: str) -> str:
    """
    Priority:
      1. If env var contains raw Netscape text  → write /tmp/<name>.txt
      2. If default_path file exists on disk    → use it
      3. Otherwise                              → return "" (no cookies)
    """
    raw = os.environ.get(env_var, "").strip()

    if raw:
        # Detect Netscape format by header line OR presence of tab chars (field separator)
        is_netscape = (
            raw.startswith("# Netscape") or
            raw.startswith("# HTTP Cookie") or
            "\t" in raw
        )
        if is_netscape:
            dest = f"/tmp/cookie_{env_var.lower()}.txt"
            os.makedirs(os.path.dirname(dest) if os.path.dirname(dest) else "/tmp", exist_ok=True)
            with open(dest, "w", encoding="utf-8") as f:
                # Ensure header line exists (some exports omit it)
                if not raw.startswith("#"):
                    f.write("# Netscape HTTP Cookie File\n")
                f.write(raw)
                if not raw.endswith("\n"):
                    f.write("\n")
            print(f"[COOKIES] {env_var} → wrote {dest} ({len(raw)} chars)", flush=True)
            return dest
        else:
            # Treat as file path
            if os.path.exists(raw):
                print(f"[COOKIES] {env_var} → file path {raw}", flush=True)
                return raw

    # Fallback to default path
    if default_path and os.path.exists(default_path):
        print(f"[COOKIES] {env_var} → default {default_path}", flush=True)
        return default_path

    print(f"[COOKIES] {env_var} → none", flush=True)
    return ""

# Resolve all cookies before any downloader import
Config.YT_COOKIE = _write_cookie("YT_COOKIES",        Config.YT_COOKIE)
Config.IG_COOKIE = _write_cookie("INSTAGRAM_COOKIES", Config.IG_COOKIE)
Config.TB_COOKIE = _write_cookie("TERABOX_COOKIES",   Config.TB_COOKIE)

# ── 3. Import client + plugins (registers all @app.on_message handlers) ───────
from client import app
import plugins.start     # noqa
import plugins.download  # noqa
import plugins.admin     # noqa

import database as db
from queue_manager import queue
from pyrogram import idle

log = logging.getLogger(__name__)

# ── Main ──────────────────────────────────────────────────────────────────────
async def main():
    await db.init()
    await queue.start()

    # KEY: explicit start/stop — NOT `async with app:`
    # `async with` can silently drop decorator-registered handlers in Pyrogram 2.x
    await app.start()

    me = await app.get_me()
    Config.BOT_USERNAME = me.username

    if Config.LOG_CHANNEL:
        try:
            await app.send_message(
                Config.LOG_CHANNEL,
                f"»»──── 🟢 Bot Online ────««\n\n"
                f"🤖 @{me.username}\n"
                f"🕐 {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
                f"🍪 YT cookie : {'✅' if Config.YT_COOKIE else '❌'}\n"
                f"🍪 TB cookie : {'✅' if Config.TB_COOKIE else '❌'}"
            )
        except Exception as e:
            log.warning("Log channel: %s", e)

    print(f"""
╔══════════════════════════════════════════════════╗
║  ✅  BOT IS ONLINE & RUNNING                     ║
║  ⋆｡° ✮   SERENA DOWNLOADER BOT   ✮ °｡⋆         ║
║  Bot     : @{me.username:<35}║
║  Owner   : @Xioqui_Xan                          ║
║  Support : @TechnicalSerena                     ║
║  YT Cookie : {'✅ Active' if Config.YT_COOKIE else '❌ None':<33}║
║  TB Cookie : {'✅ Active' if Config.TB_COOKIE else '❌ None':<33}║
╚══════════════════════════════════════════════════╝
""", flush=True)

    await idle()
    await app.stop()
    await queue.stop()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("[INFO] Stopped.", flush=True)
    except Exception as e:
        print(f"[FATAL] {e}", flush=True)
        log.critical("Fatal: %s", e, exc_info=True)
        sys.exit(1)
