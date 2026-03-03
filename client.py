"""
Shared Pyrogram Client.

in_memory=True  — no .session file on disk.
                  Required for Render / stateless deployments.
                  Prevents stale-session silent message drops.
"""
from pyrogram import Client
from config import Config

app = Client(
    name            = "SerenaBot",
    api_id          = Config.API_ID,
    api_hash        = Config.API_HASH,
    bot_token       = Config.BOT_TOKEN,
    in_memory       = True,          # ← THE FIX
    workers         = 10,
    sleep_threshold = 60,
)
