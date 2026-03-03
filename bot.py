import asyncio
import os
import threading
from config import YT_COOKIES, INSTAGRAM_COOKIES, TERABOX_COOKIES

BANNER = """
╔══════════════════════════════════════════╗
║   𝗦𝗲𝗿𝗲𝗻𝗮 𝗗𝗼𝘄𝗻𝗹𝗼𝗮𝗱𝗲𝗿 𝗕𝗼𝘁              ║
║   @Universal_DownloadBot                 ║
║   Owner : @Xioqui_Xan                    ║
║   Support: @TechnicalSerena              ║
╚══════════════════════════════════════════╝
"""


def resolve_cookies():
    """
    Write cookie env vars to /tmp files so yt-dlp can read them.
    Handles both actual newlines and \\n-escaped newlines from Render.
    """
    mapping = {
        "YT_COOKIES":        ("/tmp/yt_cookies.txt",  YT_COOKIES),
        "INSTAGRAM_COOKIES": ("/tmp/ig_cookies.txt",  INSTAGRAM_COOKIES),
        "TERABOX_COOKIES":   ("/tmp/tb_cookies.txt",  TERABOX_COOKIES),
    }
    for name, (path, raw) in mapping.items():
        if not raw or not raw.strip():
            continue
        # Render stores multiline env vars with literal \n — fix that
        raw = raw.replace("\\n", "\n").strip()
        # Accept any cookie content (Netscape header optional)
        with open(path, "w", encoding="utf-8") as f:
            f.write(raw)
        print(f"[COOKIES] {name} → {path} ({len(raw)} chars)")


async def main():
    print(BANNER)
    resolve_cookies()

    # Init database
    import database
    await database.init_db()
    print("[DB] Database ready")

    # Import ALL plugins BEFORE app.start() — decorators register at import time
    import plugins.start     # noqa: F401
    import plugins.download  # noqa: F401
    import plugins.admin     # noqa: F401
    import plugins.reactions # noqa: F401
    print("[PLUGINS] All plugins loaded")

    # Start Flask keep-alive (required for Render Web Service)
    from web.app import run as flask_run
    t = threading.Thread(target=flask_run, daemon=True)
    t.start()
    print(f"[WEB] Flask keep-alive running")

    # Start Pyrogram
    from client import app
    await app.start()
    me = await app.get_me()
    print(f"[BOT] @{me.username} is online! ✅")

    await asyncio.get_event_loop().create_future()   # run forever


if __name__ == "__main__":
    asyncio.run(main())
