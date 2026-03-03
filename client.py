"""Shared Pyrogram Client — imported by all plugins."""
from pyrogram import Client
from config import Config

app = Client(
    name            = "SerenaBot",
    api_id          = Config.API_ID,
    api_hash        = Config.API_HASH,
    bot_token       = Config.BOT_TOKEN,
    workers         = 10,
    sleep_threshold = 60,
)
