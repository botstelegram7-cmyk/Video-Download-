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
from pyrogram import Client
from config import Config
import database as db
from queue_manager import queue_manager
from web.app import start_flask_thread

# ──── Handlers (import triggers registration) ────
import handlers.start
import handlers.download
import handlers.admin

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s │ %(name)-20s │ %(levelname)-8s │ %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
    ]
)
logger = logging.getLogger(__name__)

# ──────────── Pyrogram App ────────────
app = Client(
    "SerenaDownloaderBot",
    api_id=Config.API_ID,
    api_hash=Config.API_HASH,
    bot_token=Config.BOT_TOKEN,
    workers=8,
    sleep_threshold=60,
)

async def startup():
    logger.info("»»──── 🚀 Starting Bot ────««")

    # Init database
    await db.init_db()
    logger.info("✅ Database ready")

    # Start queue worker
    await queue_manager.start()
    logger.info("✅ Queue manager ready")

    # Start Flask in background thread
    start_flask_thread()
    logger.info(f"✅ Web server started on port {Config.PORT}")

    # Get bot info
    me = await app.get_me()
    Config.BOT_USERNAME = me.username
    logger.info(f"✅ Bot started as @{me.username}")

    # Log to channel
    if Config.LOG_CHANNEL:
        try:
            await app.send_message(
                Config.LOG_CHANNEL,
                f"»»──── 🤖 Bot Started ────««\n\n"
                f"🤖 @{me.username} is **online**!\n"
                f"🕐 {__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            )
        except Exception as e:
            logger.warning(f"Log channel send failed: {e}")

    print("""
╔══════════════════════════════════════════╗
║   ✅  BOT IS NOW ONLINE & RUNNING!       ║
║   ⋆｡° ✮  SERENA DOWNLOADER  ✮ °｡⋆      ║
╚══════════════════════════════════════════╝
    """)

async def shutdown():
    await queue_manager.stop()
    logger.info("»»──── 🛑 Bot Stopped ────««")

async def main():
    if not Config.validate():
        logger.error("❌ Invalid configuration! Check your environment variables.")
        sys.exit(1)

    async with app:
        await startup()
        await asyncio.Event().wait()  # Keep running until interrupted

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot stopped by user (KeyboardInterrupt)")
    except Exception as e:
        logger.critical(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)
