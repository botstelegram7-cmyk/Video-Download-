"""
╔══════════════════════════════════════════╗
║       🔒  D E C O R A T O R S               ║
╚══════════════════════════════════════════╝
"""
import logging, functools
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from config import Config
from utils.helpers import is_owner, is_subscribed
import database as db

logger = logging.getLogger(__name__)

def owner_only(func):
    @functools.wraps(func)
    async def wrapper(client, message: Message, *args, **kwargs):
        if not is_owner(message.from_user.id):
            await message.reply(
                "»»──── 🚫 Access Denied ────««\nOwner only command.", quote=True)
            return
        return await func(client, message, *args, **kwargs)
    return wrapper

def check_ban(func):
    @functools.wraps(func)
    async def wrapper(client, message: Message, *args, **kwargs):
        uid  = message.from_user.id
        user = await db.get_user(uid)
        if user and user.get("is_banned"):
            await message.reply(
                f"»»──── 🚫 Banned ────««\nContact {Config.OWNER_USERNAME}.", quote=True)
            return
        return await func(client, message, *args, **kwargs)
    return wrapper

def force_subscribe(func):
    @functools.wraps(func)
    async def wrapper(client, message: Message, *args, **kwargs):
        uid = message.from_user.id
        if is_owner(uid):
            return await func(client, message, *args, **kwargs)
        if not await is_subscribed(client, uid):
            btn = InlineKeyboardMarkup([[
                InlineKeyboardButton("📢 Join Channel", url=Config.FORCE_SUB_CHANNEL),
                InlineKeyboardButton("✅ I Joined", callback_data="check_sub")
            ]])
            await message.reply(
                "»»──── 🔔 JOIN REQUIRED ──────««\n\n"
                "Join our channel first, then click **✅ I Joined**.",
                reply_markup=btn, quote=True)
            return
        return await func(client, message, *args, **kwargs)
    return wrapper

def check_limit(func):
    @functools.wraps(func)
    async def wrapper(client, message: Message, *args, **kwargs):
        uid = message.from_user.id
        if is_owner(uid):
            return await func(client, message, *args, **kwargs)
        user = await db.check_and_reset_daily(uid)
        if not user:
            await db.upsert_user(uid, message.from_user.username, message.from_user.first_name)
            user = await db.get_user(uid)
        used, limit = await db.get_user_limit(user)
        if used >= limit:
            plan = user.get("plan", "free")
            await message.reply(
                f"»»──── ⚠️ Daily Limit Reached ────««\n\n"
                f"📊 Used : **{used} / {limit}** today\n"
                f"🏷️  Plan : **{plan.capitalize()}**\n\n"
                f"Upgrade for more downloads!\n"
                f"✦ Basic → 3/day • Premium → 50/day",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("💎 Get Premium", callback_data="buy_premium"),
                    InlineKeyboardButton("👑 Owner", url=f"https://t.me/{Config.OWNER_USERNAME.strip('@')}"),
                ]]),
                quote=True
            )
            return
        return await func(client, message, *args, **kwargs)
    return wrapper
