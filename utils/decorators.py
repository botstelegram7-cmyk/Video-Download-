"""Auth decorators: owner_only, anti_ban, force_subscribe, rate_limit."""
import functools, logging
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from config import Config
from utils.helpers import is_owner, is_subbed, plan_badge
import database as db

log = logging.getLogger(__name__)

def owner_only(fn):
    @functools.wraps(fn)
    async def wrap(client, msg: Message, *a, **kw):
        if not is_owner(msg.from_user.id):
            await msg.reply("🚫 **Owner only command.**", quote=True)
            return
        return await fn(client, msg, *a, **kw)
    return wrap

def guard(fn):
    """Stacks: ban check → force-sub → daily limit."""
    @functools.wraps(fn)
    async def wrap(client, msg: Message, *a, **kw):
        uid  = msg.from_user.id
        user = await db.reset_if_new_day(uid)

        # ── create user if first time ──────────────────────
        if not user:
            user = await db.ensure_user(uid, msg.from_user.username or "", msg.from_user.first_name or "")

        # ── ban check ──────────────────────────────────────
        if user and user.get("is_banned"):
            await msg.reply(
                f"🚫 **You are banned.**\n\nContact @{Config.OWNER_UNAME} for appeal.",
                quote=True
            )
            return

        # ── force subscribe ────────────────────────────────
        if not is_owner(uid) and Config.FSUB_ID:
            if not await is_subbed(client, uid):
                await msg.reply(
                    "»»──── 🔔 JOIN REQUIRED ────««\n\n"
                    "Please join our channel first,\nthen send the link again.",
                    reply_markup=InlineKeyboardMarkup([[
                        InlineKeyboardButton("📢 Join Channel", url=Config.FSUB_LINK),
                        InlineKeyboardButton("✅ Joined",        callback_data="check_sub"),
                    ]]),
                    quote=True
                )
                return

        # ── daily limit ────────────────────────────────────
        if not is_owner(uid):
            used, lim = await db.get_limit(user)
            if used >= lim:
                plan = user.get("plan", "free")
                await msg.reply(
                    "»»──── ⚠️ Limit Reached ────««\n\n"
                    f"📊 Used today : **{used} / {lim}**\n"
                    f"🏷️  Your plan  : **{plan_badge(plan)}**\n\n"
                    "Upgrade to download more!",
                    reply_markup=InlineKeyboardMarkup([[
                        InlineKeyboardButton("💎 Get Premium",
                                             url=f"https://t.me/{Config.OWNER_UNAME}"),
                    ]]),
                    quote=True
                )
                return

        return await fn(client, msg, *a, **kw)
    return wrap
