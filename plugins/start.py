"""
╔══════════════════════════════════════════╗
║   🚀  S T A R T  &  H E L P  H A N D L E R ║
╚══════════════════════════════════════════╝
"""
import logging
from datetime import datetime
from pyrogram import filters
from pyrogram.types import (
    Message, CallbackQuery,
    InlineKeyboardMarkup, InlineKeyboardButton
)
from client import app
from config import Config
import database as db
from utils.helpers import is_owner, is_subscribed, plan_badge, format_datetime

logger = logging.getLogger(__name__)
BOT_START_TIME = datetime.now()

def uptime_str() -> str:
    delta = datetime.now() - BOT_START_TIME
    days    = delta.days
    hours   = delta.seconds // 3600
    minutes = (delta.seconds % 3600) // 60
    return f"{days}d {hours}h {minutes}m"

# ═════════════════════════════════════════
#  /start
# ═════════════════════════════════════════
@app.on_message(filters.command("start") & filters.private)
async def start_cmd(client, message: Message):
    user = message.from_user
    try:
        await db.get_or_create_user(user.id, user.username, user.first_name)
    except Exception as e:
        logger.error(f"DB error in start: {e}")

    # ── Force subscribe check ──────────────────────────────
    if not is_owner(user.id) and Config.FORCE_SUB_CHANNEL_ID:
        try:
            subscribed = await is_subscribed(client, user.id)
        except:
            subscribed = True

        if not subscribed:
            btn = InlineKeyboardMarkup([[
                InlineKeyboardButton("📢 Join Channel", url=Config.FORCE_SUB_CHANNEL),
                InlineKeyboardButton("✅ I Joined",     callback_data="check_sub"),
            ]])
            text = (
                f"⋆｡° ✮ °｡⋆\n"
                f"-ˏˋ⋆ ᴡ ᴇ ʟ ᴄ ᴏ ᴍ ᴇ ⋆ˊˎ-\n\n"
                f"🌸 Hello **{user.first_name}**!\n\n"
                f"⚠️ You must join our channel to use this bot.\n"
                f"Click **Join Channel** then **✅ I Joined**."
            )
            try:
                if Config.START_PIC:
                    await message.reply_photo(photo=Config.START_PIC, caption=text, reply_markup=btn)
                else:
                    await message.reply(text, reply_markup=btn)
            except Exception as e:
                logger.error(f"Start force-sub reply error: {e}")
                await message.reply(text, reply_markup=btn)
            return

    # ── Main start message ─────────────────────────────────
    try:
        db_user = await db.get_user(user.id)
        plan    = db_user.get("plan", "free") if db_user else "free"
    except:
        plan = "free"

    await _send_start_message(client, message, user, plan)

async def _send_start_message(client, message, user, plan):
    buttons = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("📖 Help & Commands", callback_data="help_main"),
            InlineKeyboardButton("💎 Plans & Pricing", callback_data="plans_info"),
        ],
        [
            InlineKeyboardButton("📊 My Stats",        callback_data="my_stats"),
            InlineKeyboardButton("📜 My History",      callback_data="my_history"),
        ],
        [
            InlineKeyboardButton("🔔 Updates Channel", url=Config.FORCE_SUB_CHANNEL),
            InlineKeyboardButton("⚙️ Settings",        callback_data="settings_menu"),
        ],
        [
            InlineKeyboardButton("👑 Owner",   url=f"https://t.me/{Config.OWNER_USERNAME.strip('@')}"),
            InlineKeyboardButton("📞 Support", url=f"https://t.me/{Config.OWNER_USERNAME2.strip('@')}"),
        ],
    ])

    caption = (
        f"⋆｡° ✮ °｡⋆\n"
        f"-ˏˋ⋆ ᴡ ᴇ ʟ ᴄ ᴏ ᴍ ᴇ ⋆ˊˎ-\n\n"
        f"✨ Hello **{user.first_name}**! I am\n"
        f"**{Config.BOT_NAME}**\n\n"
        f"»»──── 🌐 What I Can Download ────««\n"
        f"▸ 🎥 YouTube (Video / Shorts / Playlist)\n"
        f"▸ 📸 Instagram (Reels / Posts / Stories)\n"
        f"▸ 🎵 TikTok / Twitter / Facebook\n"
        f"▸ 📦 Terabox (Any Terabox Link)\n"
        f"▸ 🌊 M3U8 / HLS Streams\n"
        f"▸ 🔗 Any Direct Download Link\n"
        f"▸ 📄 .txt File with Multiple Links\n"
        f"▸ 🌐 1000+ Sites via yt-dlp\n\n"
        f"»»──── 🎯 Extra Features ────««\n"
        f"▸ 🎵 Audio-Only Mode (/audio)\n"
        f"▸ ℹ️  URL Info (/info)\n"
        f"▸ 📋 Download History (/history)\n"
        f"▸ ⏱  Real-Time Progress Bars\n"
        f"▸ 🖼️  Auto Thumbnail & Metadata\n\n"
        f"🏷️  Your Plan : **{plan_badge(plan)}**\n"
        f"⋆ ｡˚ Send any link to start downloading! ˚｡ ⋆\n\n"
        f"»»────── {Config.DIVIDER_SM} ──────««"
    )

    try:
        if Config.START_PIC:
            await message.reply_photo(photo=Config.START_PIC, caption=caption, reply_markup=buttons)
        else:
            await message.reply(caption, reply_markup=buttons)
    except Exception as e:
        logger.error(f"Start message send error: {e}")
        try:
            await message.reply(caption, reply_markup=buttons)
        except Exception as e2:
            logger.error(f"Fallback start message failed: {e2}")

# ═════════════════════════════════════════
#  /help
# ═════════════════════════════════════════
@app.on_message(filters.command("help") & filters.private)
async def help_cmd(client, message: Message):
    await _send_help(message)

async def _send_help(target):
    """Send help message. target = Message or CallbackQuery."""
    text = (
        f"»»────── 📖 HELP MENU ──────««\n\n"
        f"⋆｡° ✮ **HOW TO USE** ✮ °｡⋆\n\n"
        f"Just send me any **link** and I'll download it!\n\n"
        f"»»────── 📥 Supported Sources ──────««\n"
        f"  🎥  YouTube (video / shorts / playlist)\n"
        f"  📸  Instagram (reels / posts / stories)\n"
        f"  🎵  TikTok / Twitter-X / Facebook\n"
        f"  📦  Terabox (any link)\n"
        f"  🌊  M3U8 / HLS streams\n"
        f"  🔗  Any direct download link (.mp4, .mp3…)\n"
        f"  📄  .txt files with multiple links\n"
        f"  🌐  1000+ sites via yt-dlp\n\n"
        f"»»────── ⌨️ User Commands ──────««\n"
        f"  /start      — Welcome & main menu\n"
        f"  /help       — This help menu\n"
        f"  /audio URL  — Download audio only 🎵\n"
        f"  /info URL   — Get URL info (no download)\n"
        f"  /history    — Your download history\n"
        f"  /mystats    — Your stats & quota\n"
        f"  /queue      — View active downloads\n"
        f"  /cancel     — Cancel your downloads\n"
        f"  /status     — Bot status & uptime\n"
        f"  /plans      — View plans & pricing\n"
        f"  /buy        — Buy a premium plan\n"
        f"  /ping       — Check bot response\n"
        f"  /feedback   — Send feedback to owner\n\n"
        f"»»────── 👑 Admin Commands ──────««\n"
        f"  /givepremium [id] [plan]\n"
        f"  /removepremium [id]\n"
        f"  /ban [id]  |  /unban [id]\n"
        f"  /broadcast [msg]\n"
        f"  /stats  |  /users  |  /banned\n"
        f"  /restart — Restart the bot\n\n"
        f"»»──────────────────────────────««\n"
        f"⋆ ｡˚ Owned by {Config.OWNER_USERNAME} ˚｡ ⋆"
    )
    btn = InlineKeyboardMarkup([[
        InlineKeyboardButton("🏠 Back to Home", callback_data="back_home"),
        InlineKeyboardButton("💎 Plans",        callback_data="plans_info"),
    ]])
    if hasattr(target, "from_user"):  # it's a Message
        await target.reply(text, reply_markup=btn, quote=True)
    else:  # it's a CallbackQuery
        try:
            await target.message.edit_text(text, reply_markup=btn)
        except:
            await target.message.reply(text, reply_markup=btn)

# ═════════════════════════════════════════
#  /ping
# ═════════════════════════════════════════
@app.on_message(filters.command("ping") & filters.private)
async def ping_cmd(client, message: Message):
    import time
    start = time.time()
    sent  = await message.reply("🏓 Pong!", quote=True)
    ms    = int((time.time() - start) * 1000)
    await sent.edit_text(
        f"»»──── 🏓 PONG ────««\n\n"
        f"  ⚡ Response : **{ms} ms**\n"
        f"  ⏰ Uptime   : **{uptime_str()}**\n\n"
        f"»»──────────────────««"
    )

# ═════════════════════════════════════════
#  /status
# ═════════════════════════════════════════
@app.on_message(filters.command("status") & filters.private)
async def status_cmd(client, message: Message):
    try:
        total_users = await db.get_total_users()
        total_dls   = await db.get_total_downloads()
        me          = await client.get_me()
        text = (
            f"»»────── 📊 BOT STATUS ──────««\n\n"
            f"🤖 Bot     : @{me.username}\n"
            f"⏰ Uptime  : **{uptime_str()}**\n"
            f"👥 Users   : **{total_users}**\n"
            f"📥 Done DLs: **{total_dls}**\n\n"
            f"⋆ ｡˚ Everything running smoothly! ˚｡ ⋆\n\n"
            f"»»──────────────────────────««"
        )
    except Exception as e:
        text = f"»»──── 📊 STATUS ────««\n\n⏰ Uptime: **{uptime_str()}**\n\n»»──────────────────««"
    await message.reply(text, quote=True)

# ═════════════════════════════════════════
#  /plans  /buy
# ═════════════════════════════════════════
@app.on_message(filters.command(["plans", "buy"]) & filters.private)
async def plans_cmd(client, message: Message):
    await _send_plans(message)

async def _send_plans(target):
    text = (
        f"»»────── 💎 PLANS & PRICING ──────««\n\n"
        f"🆓 **Free Plan**\n"
        f"   ▸ {Config.FREE_DAILY_LIMIT} downloads / day\n"
        f"   ▸ All basic sites\n\n"
        f"🥉 **Basic Plan** — _1 Month_\n"
        f"   ▸ {Config.BASIC_DAILY_LIMIT} downloads / day\n"
        f"   ▸ All sites + Terabox\n"
        f"   ▸ Priority queue\n"
        f"   ▸ Faster processing\n\n"
        f"💎 **Premium Plan** — _1 Year_\n"
        f"   ▸ {Config.PREMIUM_DAILY_LIMIT} downloads / day\n"
        f"   ▸ All features + VIP support\n"
        f"   ▸ Highest priority queue\n"
        f"   ▸ Unlimited file size (within Telegram limit)\n\n"
        f"»»────── 💳 HOW TO BUY ──────««\n"
        f"  1️⃣  Contact owner or support\n"
        f"  2️⃣  Pay via UPI / QR / Crypto\n"
        f"  3️⃣  Send payment screenshot\n"
        f"  4️⃣  Plan activated instantly! 🎉\n\n"
        f"»»──────────────────────────────««"
    )
    btn = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("👑 Contact Owner", url=f"https://t.me/{Config.OWNER_USERNAME.strip('@')}"),
            InlineKeyboardButton("📞 Support",       url=f"https://t.me/{Config.OWNER_USERNAME2.strip('@')}"),
        ],
        [InlineKeyboardButton("🏠 Back", callback_data="back_home")]
    ])
    if hasattr(target, "from_user"):
        await target.reply(text, reply_markup=btn, quote=True)
    else:
        try:
            await target.message.edit_text(text, reply_markup=btn)
        except:
            await target.message.reply(text, reply_markup=btn)

# ═════════════════════════════════════════
#  /mystats
# ═════════════════════════════════════════
@app.on_message(filters.command("mystats") & filters.private)
async def mystats_cmd(client, message: Message):
    await _send_mystats(message, message.from_user.id)

async def _send_mystats(message, user_id: int):
    try:
        user = await db.check_and_reset_daily(user_id)
        if not user:
            await message.reply("Please /start the bot first.", quote=True)
            return
        used, limit = await db.get_user_limit(user)
        plan   = user.get("plan", "free")
        expiry = (user.get("plan_expiry") or "")[:10] or "—"
        joined = (user.get("joined_at")   or "")[:10] or "—"
        total_dls = await db.get_total_downloads()

        # Usage bar
        bar_len   = 10
        filled    = int((used / limit) * bar_len) if limit > 0 else 0
        usage_bar = "🟩" * filled + "⬜" * (bar_len - filled)

        text = (
            f"»»────── 👤 MY STATS ──────««\n\n"
            f"🆔 ID       : `{user_id}`\n"
            f"🏷️  Plan     : **{plan_badge(plan)}**\n"
            f"📅 Expires  : **{expiry}**\n"
            f"🗓️  Joined   : **{joined}**\n\n"
            f"»»────── 📊 Today's Usage ──────««\n"
            f"  {usage_bar}\n"
            f"  📥 {used} / {limit} downloads used\n\n"
            f"»»──────────────────────────««"
        )
        btn = InlineKeyboardMarkup([[
            InlineKeyboardButton("💎 Upgrade", callback_data="plans_info"),
            InlineKeyboardButton("📜 History", callback_data="my_history"),
            InlineKeyboardButton("🏠 Home",    callback_data="back_home"),
        ]])
        await message.reply(text, reply_markup=btn, quote=True)
    except Exception as e:
        logger.error(f"mystats error: {e}")
        await message.reply("❌ Could not fetch stats. Try again.", quote=True)

# ═════════════════════════════════════════
#  /history
# ═════════════════════════════════════════
@app.on_message(filters.command("history") & filters.private)
async def history_cmd(client, message: Message):
    await _send_history(message, message.from_user.id)

async def _send_history(message, user_id: int):
    try:
        downloads = await db.get_user_downloads(user_id, limit=10)
        if not downloads:
            await message.reply(
                "»»────── 📜 HISTORY ──────««\n\n"
                "No downloads yet! Send a link to get started.\n\n"
                "»»──────────────────────────««",
                quote=True
            )
            return
        lines = ["»»────── 📜 DOWNLOAD HISTORY ──────««\n"]
        for i, dl in enumerate(downloads, 1):
            fname = (dl.get("file_name") or "Unknown")[:30]
            date  = (dl.get("created_at") or "")[:10]
            lines.append(f"  {i}. 📄 `{fname}`\n     📅 {date}")
        lines.append("\n»»──────────────────────────────««")
        await message.reply("\n".join(lines), quote=True)
    except Exception as e:
        logger.error(f"history error: {e}")
        await message.reply("❌ Could not fetch history.", quote=True)

# ═════════════════════════════════════════
#  /feedback
# ═════════════════════════════════════════
@app.on_message(filters.command("feedback") & filters.private)
async def feedback_cmd(client, message: Message):
    user   = message.from_user
    args   = message.text.split(None, 1)
    if len(args) < 2:
        await message.reply(
            "»»──── 💬 FEEDBACK ────««\n\n"
            "Usage: `/feedback Your message here`\n\n"
            "Example: `/feedback Bot is amazing! 🔥`",
            quote=True
        )
        return
    feedback_text = args[1].strip()
    try:
        await db.save_feedback(user.id, feedback_text)
    except:
        pass

    # Forward to owner if configured
    owner_id = Config.OWNER_IDS[0] if Config.OWNER_IDS else None
    if owner_id:
        try:
            await client.send_message(
                owner_id,
                f"»»──── 💬 NEW FEEDBACK ────««\n\n"
                f"👤 From: {user.first_name} (@{user.username or '?'}) | `{user.id}`\n\n"
                f"📝 Message:\n{feedback_text}\n\n"
                f"»»──────────────────────────««"
            )
        except:
            pass

    await message.reply(
        "»»──── ✅ FEEDBACK SENT ────««\n\n"
        "Thanks! Your feedback has been sent to the owner. 💖\n\n"
        "»»──────────────────────────««",
        quote=True
    )

# ═════════════════════════════════════════
#  /settings
# ═════════════════════════════════════════
@app.on_message(filters.command("settings") & filters.private)
async def settings_cmd(client, message: Message):
    uid  = message.from_user.id
    user = await db.get_user(uid)
    plan = user.get("plan", "free") if user else "free"
    btn = InlineKeyboardMarkup([
        [InlineKeyboardButton("💎 Upgrade Plan",    callback_data="plans_info")],
        [InlineKeyboardButton("📊 My Stats",        callback_data="my_stats")],
        [InlineKeyboardButton("📜 My History",      callback_data="my_history")],
        [InlineKeyboardButton("🏠 Home",            callback_data="back_home")],
    ])
    await message.reply(
        f"»»──── ⚙️ SETTINGS ────««\n\n"
        f"🏷️  Plan    : **{plan_badge(plan)}**\n"
        f"🆔 User ID : `{uid}`\n\n"
        f"»»──────────────────────««",
        reply_markup=btn, quote=True
    )

# ═════════════════════════════════════════
#  CALLBACK QUERIES
# ═════════════════════════════════════════
@app.on_callback_query(filters.regex("^check_sub$"))
async def check_sub_cb(client, cb: CallbackQuery):
    uid = cb.from_user.id
    try:
        subscribed = await is_subscribed(client, uid)
    except:
        subscribed = True

    if subscribed:
        await cb.answer("✅ Verified! Welcome!", show_alert=True)
        try:
            await cb.message.delete()
        except:
            pass
        # ✅ FIX: Re-send the start message after verification
        try:
            db_user = await db.get_user(uid)
            plan    = db_user.get("plan", "free") if db_user else "free"
            await _send_start_message(client, cb.message, cb.from_user, plan)
        except Exception as e:
            logger.error(f"Post-join start error: {e}")
    else:
        await cb.answer("❌ You haven't joined yet! Please join first.", show_alert=True)

@app.on_callback_query(filters.regex("^back_home$"))
async def back_home_cb(client, cb: CallbackQuery):
    await cb.answer()
    try:
        await cb.message.delete()
    except:
        pass
    try:
        db_user = await db.get_user(cb.from_user.id)
        plan    = db_user.get("plan", "free") if db_user else "free"
        await _send_start_message(client, cb.message, cb.from_user, plan)
    except Exception as e:
        logger.error(f"back_home error: {e}")

@app.on_callback_query(filters.regex("^help_main$"))
async def help_cb(client, cb: CallbackQuery):
    await cb.answer()
    await _send_help(cb)

@app.on_callback_query(filters.regex("^plans_info$"))
async def plans_cb(client, cb: CallbackQuery):
    await cb.answer()
    await _send_plans(cb)

@app.on_callback_query(filters.regex("^my_stats$"))
async def my_stats_cb(client, cb: CallbackQuery):
    await cb.answer()
    # ✅ FIX: Use cb.from_user.id not cb.message.from_user.id
    await _send_mystats(cb.message, cb.from_user.id)

@app.on_callback_query(filters.regex("^my_history$"))
async def my_history_cb(client, cb: CallbackQuery):
    await cb.answer()
    await _send_history(cb.message, cb.from_user.id)

@app.on_callback_query(filters.regex("^buy_premium$"))
async def buy_premium_cb(client, cb: CallbackQuery):
    await cb.answer()
    await _send_plans(cb)

@app.on_callback_query(filters.regex("^settings_menu$"))
async def settings_menu_cb(client, cb: CallbackQuery):
    await cb.answer()
    uid  = cb.from_user.id
    user = await db.get_user(uid)
    plan = user.get("plan", "free") if user else "free"
    btn = InlineKeyboardMarkup([
        [InlineKeyboardButton("💎 Upgrade Plan",    callback_data="plans_info")],
        [InlineKeyboardButton("📊 My Stats",        callback_data="my_stats")],
        [InlineKeyboardButton("📜 My History",      callback_data="my_history")],
        [InlineKeyboardButton("🏠 Home",            callback_data="back_home")],
    ])
    try:
        await cb.message.edit_text(
            f"»»──── ⚙️ SETTINGS ────««\n\n"
            f"🏷️  Plan    : **{plan_badge(plan)}**\n"
            f"🆔 User ID : `{uid}`\n\n"
            f"»»──────────────────────««",
            reply_markup=btn
        )
    except:
        pass
