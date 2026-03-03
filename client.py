"""
Shared Pyrogram Client instance.
Imported by bot.py AND all plugin files.
"""
from pyrogram import Client
from config import Config

app = Client(
    name        = "SerenaDownloaderBot",
    api_id      = Config.API_ID,
    api_hash    = Config.API_HASH,
    bot_token   = Config.BOT_TOKEN,
    workers     = 8,
    sleep_threshold = 60,
)
