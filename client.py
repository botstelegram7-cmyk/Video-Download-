from pyrogram import Client
from config import API_ID, API_HASH, BOT_TOKEN

app = Client(
    name="SerenaBot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN,
    in_memory=True,        # CRITICAL for Render.com — no .session file
    sleep_threshold=60,
)
