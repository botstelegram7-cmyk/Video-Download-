"""
╔══════════════════════════════════════════╗
║       🔒  D E C O R A T O R S               ║
╚══════════════════════════════════════════╝
"""
import logging
import functools
from pyrogram import filters
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
                "»»──── 🚫 Access Denied ────««\n"
                "This command is for **Owner** only.",
                quote=True
            )
            return
        return await func(client, message, *args, **kwargs)
    return wrapper

def check_ban(func):
    @functools.wraps(func)
    async def wrapper(client, message: Message, *args, **kwargs):
        uid = message.from_user.id
        user = await db.get_user(uid)
        if user and user.get("is_banned"):
            await message.reply(
                "»»──── 🚫 Banned ────««\n"
                "You have been **banned** from using this bot.\n"
                f"Contact {Config.OWNER_USERNAME} for support.",
                quote=True
            )
            return
        return await func(client, message, *args, **kwargs)
    return wrapper

def force_subscribe(func):
    @functools.wraps(func)
    async def wrapper(client, message: Message, *args, **kwargs):
        uid = message.from_user.id
        if is_owner(uid):
            return await func(client, message, *args, **kwargs)
        subscribed = await is_subscribed(client, uid)
        if not subscribed:
            btn = InlineKeyboardMarkup([[
                InlineKeyboardButton("📢 Join Channel", url=Config.FORCE_SUB_CHANNEL),
                InlineKeyboardButton("✅ I Joined", callback_data="check_sub")
            ]])
            await message.reply(
                "»»────── 🔔 JOIN REQUIRED ──────««\n\n"
                "𝗣𝗹𝗲𝗮𝘀𝗲 𝗷𝗼𝗶𝗻 𝗼𝘂𝗿 𝗰𝗵𝗮𝗻𝗻𝗲𝗹 𝘁𝗼 𝘂𝘀𝗲 𝘁𝗵𝗶𝘀 𝗯𝗼𝘁!\n\n"
                "After joining, click **✅ I Joined** button.\n\n"
                "»»──────────────────────────««",
                reply_markup=btn,
                quote=True
            )
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
            upgrade_btn = InlineKeyboardMarkup([[
                InlineKeyboardButton("💎 Get Premium", callback_data="buy_premium"),
                InlineKeyboardButton("👑 Contact Owner", url=f"https://t.me/{Config.OWNER_USERNAME.strip('@')}")
            ]])
            await message.reply(
                f"»»──── ⚠️ Daily Limit Reached ────««\n\n"
                f"📊 Used   : **{used} / {limit}** downloads today\n"
                f"🏷️  Plan   : **{plan.capitalize()}**\n\n"
                f"Upgrade your plan to get more downloads!\n"
                f"✦ Basic Plan  → 3/day for 1 month\n"
                f"✦ Premium     → 50/day for 1 year\n\n"
                f"»»──────────────────────────««",
                reply_markup=upgrade_btn,
                quote=True
            )
            return
        return await func(client, message, *args, **kwargs)
    return wrapper
