import asyncio
from functools import wraps
from pyrogram.types import Message
import database as db
from utils.helpers import is_owner, is_subbed, fmt_size
from config import (FREE_LIMIT, BASIC_LIMIT, PREMIUM_LIMIT,
                    FSUB_LINK, MAX_SIZE, OWNER_IDS)


def guard(func):
    """Check ban → force-sub → daily limit before running handler."""
    @wraps(func)
    async def wrapper(client, message: Message, *args, **kwargs):
        uid  = message.from_user.id if message.from_user else 0
        user = await db.get_user(uid)

        # ── Register new user ──
        if not user:
            fn = (message.from_user.first_name or "") + " " + (message.from_user.last_name or "")
            await db.upsert_user(uid, message.from_user.username or "", fn.strip())
            user = await db.get_user(uid)

        # ── Ban check ──
        if user and user.get("is_banned"):
            await message.reply(
                "»»──── 🚫 Banned ────««\n\n"
                "You are banned from using this bot.\n"
                f"Contact @{client.SUPPORT_USERNAME if hasattr(client, 'SUPPORT_USERNAME') else 'TechnicalSerena'} to appeal."
            )
            return

        # ── Force-sub check ──
        if FSUB_LINK and not await is_subbed(client, uid):
            from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
            await message.reply(
                "»»──── 📢 Join Required ────««\n\n"
                "▸ You must join our channel first!\n\n"
                f"⋆｡° ✮ @Universal_DownloadBot ✮ °｡⋆",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("📢 Join Channel", url=FSUB_LINK),
                    InlineKeyboardButton("✅ I Joined", callback_data="check_sub"),
                ]])
            )
            return

        # ── Plan expiry ──
        await db.check_plan_expiry(uid)
        user = await db.check_and_reset_daily(uid)

        # ── Daily limit ──
        if uid not in OWNER_IDS:
            plan  = user.get("plan", "free")
            limit = {"basic": BASIC_LIMIT, "premium": PREMIUM_LIMIT}.get(plan, FREE_LIMIT)
            count = user.get("daily_count", 0)
            if count >= limit:
                badge = {"basic": "🥉", "premium": "💎"}.get(plan, "🆓")
                await message.reply(
                    f"»»──── ⚠️ Daily Limit ────««\n\n"
                    f"▸ Plan    : {badge} {plan.capitalize()}\n"
                    f"▸ Used    : {count}/{limit}\n\n"
                    "Limit resets at midnight UTC.\n"
                    "Upgrade for more downloads! /plans\n\n"
                    "⋆｡° ✮ @Universal_DownloadBot ✮ °｡⋆"
                )
                return

        return await func(client, message, *args, **kwargs)
    return wrapper


def owner_only(func):
    @wraps(func)
    async def wrapper(client, message: Message, *args, **kwargs):
        if not is_owner(message.from_user.id if message.from_user else 0):
            await message.reply("🚫 Owner only command.")
            return
        return await func(client, message, *args, **kwargs)
    return wrapper
