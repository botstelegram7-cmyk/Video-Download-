import asyncio, os, threading
from config import YT_COOKIES, INSTAGRAM_COOKIES, TERABOX_COOKIES

# ── Resolve cookies from env vars ──────────────────────────────────────────
def resolve_cookies():
    mapping = {
        "YT_COOKIES":        ("/tmp/cookie_YT_COOKIES.txt",        YT_COOKIES),
        "INSTAGRAM_COOKIES": ("/tmp/cookie_INSTAGRAM_COOKIES.txt", INSTAGRAM_COOKIES),
        "TERABOX_COOKIES":   ("/tmp/cookie_TERABOX_COOKIES.txt",   TERABOX_COOKIES),
    }
    for name, (path, raw) in mapping.items():
        raw = raw.strip()
        if raw and (raw.startswith("# Netscape") or "\t" in raw):
            with open(path, "w") as f:
                f.write(raw)
            print(f"[COOKIES] {name} → wrote {path} ({len(raw)} chars)")

# ── Startup banner ─────────────────────────────────────────────────────────
BANNER = r"""
╔════════════════════════════════════════╗
║   𝗦𝗲𝗿𝗲𝗻𝗮 𝗗𝗼𝘄𝗻𝗹𝗼𝗮𝗱𝗲𝗿 𝗕𝗼𝘁            ║
║   @Universal_DownloadBot               ║
║   Owner: @Xioqui_Xan                   ║
╚════════════════════════════════════════╝
"""


async def main():
    print(BANNER)
    resolve_cookies()

    # ── Init DB ──
    import database
    await database.init_db()

    # ── Import plugins BEFORE app.start() ──
    import plugins.start    # noqa: F401 — registers handlers at import time
    import plugins.download # noqa: F401
    import plugins.admin    # noqa: F401

    # ── Start Flask keep-alive in background thread ──
    from web.app import run as flask_run
    t = threading.Thread(target=flask_run, daemon=True)
    t.start()
    print("[WEB] Flask keep-alive started")

    # ── Start Pyrogram ──
    from client import app
    await app.start()
    print("[BOT] Serena is online!")

    await asyncio.get_event_loop().create_future()   # run forever


if __name__ == "__main__":
    asyncio.run(main())
