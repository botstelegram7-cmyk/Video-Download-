"""
Shared Pyrogram Client instance.
Imported by bot.py AND all handler files so decorators
bind to the exact same object — no plugins= magic needed.
"""
from pyrogram import Client
from config import Config

app = Client(
    name="SerenaDownloaderBot",
    api_id=Config.API_ID,
    api_hash=Config.API_HASH,
    bot_token=Config.BOT_TOKEN,
    workers=8,
    sleep_threshold=60,
    # NO plugins= here — handlers register via @app.on_message below
)
