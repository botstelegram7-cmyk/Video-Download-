"""
╔══════════════════════════════════════════╗
║   🚀  S T A R T  &  H E L P  H A N D L E R  ║
╚══════════════════════════════════════════╝
"""
import logging
from datetime import datetime
from pyrogram import Client, filters
from pyrogram.types import (
    Message, CallbackQuery,
    InlineKeyboardMarkup, InlineKeyboardButton
)
from config import Config
import database as db
from utils.helpers import is_owner, is_subscribed, plan_badge, format_datetime
from utils.decorators import check_ban

logger = logging.getLogger(__name__)

BOT_START_TIME = datetime.now()

def uptime_str() -> str:
    delta = datetime.now() - BOT_START_TIME
    days    = delta.days
    hours   = delta.seconds // 3600
    minutes = (delta.seconds % 3600) // 60
    return f"{days}d {hours}h {minutes}m"

# ─────────────── /start ───────────────
@Client.on_message(filters.command("start") & filters.private)
@check_ban
async def start_cmd(client: Client, message: Message):
    user = message.from_user
    await db.get_or_create_user(user.id, user.username, user.first_name)

    # Force Subscribe Check
    if not is_owner(user.id):
        subscribed = await is_subscribed(client, user.id)
        if not subscribed:
            btn = InlineKeyboardMarkup([[
                InlineKeyboardButton("📢 Join Channel", url=Config.FORCE_SUB_CHANNEL),
                InlineKeyboardButton("✅ I Joined", callback_data="check_sub")
            ]])
            await message.reply_photo(
                photo=Config.START_PIC or "https://telegra.ph/file/your-default-banner.jpg",
                caption=(
                    f"-ˏˋ⋆ ᴡ ᴇ ʟ ᴄ ᴏ ᴍ ᴇ ⋆ˊˎ-\n\n"
                    f"🌸 Hello **{user.first_name}**!\n\n"
                    f"⚠️ You must join our channel to use this bot.\n"
                    f"Please join and click **✅ I Joined**."
                ),
                reply_markup=btn
            )
            return

    db_user = await db.get_user(user.id)
    plan    = db_user.get("plan", "free") if db_user else "free"

    buttons = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("📖 Help & Commands", callback_data="help_main"),
            InlineKeyboardButton("💎 Plans & Pricing", callback_data="plans_info"),
        ],
        [
            InlineKeyboardButton("📊 My Stats", callback_data="my_stats"),
            InlineKeyboardButton("🔔 Updates", url=Config.FORCE_SUB_CHANNEL),
        ],
        [
            InlineKeyboardButton("👑 Owner", url=f"https://t.me/{Config.OWNER_USERNAME.strip('@')}"),
            InlineKeyboardButton("📞 Support", url=f"https://t.me/{Config.OWNER_USERNAME2.strip('@')}"),
        ],
    ])

    caption = (
        f"⋆｡° ✮ °｡⋆\n"
        f"-ˏˋ⋆ ᴡ ᴇ ʟ ᴄ ᴏ ᴍ ᴇ ⋆ˊˎ-\n\n"
        f"✨ Hello **{user.first_name}**! I am\n"
        f"**{Config.BOT_NAME}**\n\n"
        f"»»──── 🌐 What I Can Do ────««\n"
        f"▸ YouTube, Instagram, Terabox\n"
        f"▸ M3U8 / HLS Streams\n"
        f"▸ Any Direct Download Link\n"
        f"▸ .txt File with Multiple Links\n"
        f"▸ Telegram-Playable Videos\n"
        f"▸ Auto Thumbnail + Metadata\n\n"
        f"🏷️  Your Plan : **{plan_badge(plan)}**\n"
        f"⋆ ｡˚ ⋆  Send any link to get started!  ⋆ ˚｡ ⋆\n\n"
        f"»»────── {Config.DIVIDER_SM} ──────««"
    )

    try:
        if Config.START_PIC:
            await message.reply_photo(photo=Config.START_PIC, caption=caption, reply_markup=buttons)
        else:
            await message.reply(caption, reply_markup=buttons)
    except Exception:
        await message.reply(caption, reply_markup=buttons)

# ─────────────── /help ───────────────
@Client.on_message(filters.command("help") & filters.private)
async def help_cmd(client: Client, message: Message):
    await send_help(message)

async def send_help(message: Message):
    text = (
        f"»»──────── 📖 HELP MENU ────────««\n\n"
        f"⋆｡° ✮ **HOW TO USE** ✮ °｡⋆\n\n"
        f"Just send me any **link** and I'll download it!\n\n"
        f"»»────── 📥 Supported Sources ──────««\n"
        f"  🎥  YouTube (video / shorts / playlist)\n"
        f"  📸  Instagram (reels / posts / stories)\n"
        f"  📦  Terabox (any terabox link)\n"
        f"  🌊  M3U8 / HLS streams\n"
        f"  🔗  Any direct download link\n"
        f"  📄  .txt files with multiple links\n"
        f"  🌐  1000+ sites via yt-dlp\n\n"
        f"»»────── ⌨️ Commands ──────««\n"
        f"  /start      — Welcome message\n"
        f"  /help       — This menu\n"
        f"  /cancel     — Cancel your downloads\n"
        f"  /mystats    — Your download stats\n"
        f"  /queue      — View your queue\n"
        f"  /status     — Bot status & uptime\n"
        f"  /plans      — View plans & pricing\n"
        f"  /buy        — Buy a plan\n"
        f"  /settings   — Your preferences\n\n"
        f"»»────── 👑 Admin Commands ──────««\n"
        f"  /givepremium [id] [plan] — Grant plan\n"
        f"  /removepremium [id]      — Remove plan\n"
        f"  /ban [id]                — Ban user\n"
        f"  /unban [id]              — Unban user\n"
        f"  /broadcast [msg]         — Broadcast\n"
        f"  /stats                   — Bot statistics\n"
        f"  /users                   — List premium users\n\n"
        f"»»──────────────────────────────««"
    )
    btn = InlineKeyboardMarkup([[
        InlineKeyboardButton("🏠 Back to Home", callback_data="back_home"),
        InlineKeyboardButton("💎 Plans", callback_data="plans_info"),
    ]])
    await message.reply(text, reply_markup=btn, quote=True)

# ─────────────── /status ───────────────
@Client.on_message(filters.command("status") & filters.private)
async def status_cmd(client: Client, message: Message):
    total_users = await db.get_total_users()
    total_dls   = await db.get_total_downloads()
    me          = await client.get_me()
    text = (
        f"»»────── 📊 BOT STATUS ──────««\n\n"
        f"🤖 Bot     : @{me.username}\n"
        f"⏰ Uptime  : **{uptime_str()}**\n"
        f"👥 Users   : **{total_users}**\n"
        f"📥 DLs     : **{total_dls}**\n\n"
        f"⋆ ｡˚  Everything running smoothly!  ˚｡ ⋆\n\n"
        f"»»──────────────────────────««"
    )
    await message.reply(text, quote=True)

# ─────────────── /plans ───────────────
@Client.on_message(filters.command(["plans", "buy"]) & filters.private)
async def plans_cmd(client: Client, message: Message):
    await show_plans(message)

async def show_plans(message: Message):
    text = (
        f"»»────── 💎 PLANS & PRICING ──────««\n\n"
        f"🆓 **Free Plan**\n"
        f"   ▸ {Config.BASIC_DAILY_LIMIT} downloads / day\n"
        f"   ▸ Basic sites supported\n"
        f"   ▸ Standard quality\n\n"
        f"🥉 **Basic Plan** — _1 Month_\n"
        f"   ▸ {Config.BASIC_DAILY_LIMIT} downloads / day\n"
        f"   ▸ All sites + Terabox\n"
        f"   ▸ Priority queue\n"
        f"   ▸ Contact owner for pricing\n\n"
        f"💎 **Premium Plan** — _1 Year_\n"
        f"   ▸ {Config.PREMIUM_DAILY_LIMIT} downloads / day\n"
        f"   ▸ All sites + all features\n"
        f"   ▸ Fastest servers\n"
        f"   ▸ VIP support\n"
        f"   ▸ Contact owner for pricing\n\n"
        f"»»────── 💳 HOW TO BUY ──────««\n"
        f"  1️⃣  Contact owner / support\n"
        f"  2️⃣  Pay via UPI / QR\n"
        f"  3️⃣  Send payment screenshot\n"
        f"  4️⃣  Get plan activated instantly!\n\n"
        f"»»──────────────────────────────««"
    )
    btn = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("👑 Contact Owner", url=f"https://t.me/{Config.OWNER_USERNAME.strip('@')}"),
            InlineKeyboardButton("📞 Support", url=f"https://t.me/{Config.OWNER_USERNAME2.strip('@')}"),
        ],
        [InlineKeyboardButton("🏠 Back", callback_data="back_home")]
    ])
    await message.reply(text, reply_markup=btn, quote=True)

# ─────────────── /mystats ───────────────
@Client.on_message(filters.command("mystats") & filters.private)
async def mystats_cmd(client: Client, message: Message):
    uid  = message.from_user.id
    user = await db.check_and_reset_daily(uid)
    if not user:
        await message.reply("Please /start the bot first.", quote=True)
        return
    used, limit = await db.get_user_limit(user)
    plan    = user.get("plan", "free")
    expiry  = user.get("plan_expiry", "")[:10] if user.get("plan_expiry") else "—"
    joined  = (user.get("joined_at") or "")[:10]
    text = (
        f"»»────── 👤 MY STATS ──────««\n\n"
        f"🆔 ID       : `{uid}`\n"
        f"🏷️  Plan     : **{plan_badge(plan)}**\n"
        f"📅 Expires  : **{expiry}**\n"
        f"📥 Today    : **{used} / {limit}** downloads\n"
        f"🗓️  Joined   : **{joined}**\n\n"
        f"»»──────────────────────────««"
    )
    btn = InlineKeyboardMarkup([[
        InlineKeyboardButton("💎 Upgrade", callback_data="plans_info"),
        InlineKeyboardButton("🏠 Home", callback_data="back_home"),
    ]])
    await message.reply(text, reply_markup=btn, quote=True)

# ─────────────── Callbacks ───────────────
@Client.on_callback_query(filters.regex("^check_sub$"))
async def check_sub_cb(client: Client, cb: CallbackQuery):
    uid = cb.from_user.id
    subscribed = await is_subscribed(client, uid)
    if subscribed:
        await cb.answer("✅ Verified! You can now use the bot.", show_alert=True)
        await cb.message.delete()
        fake_msg = cb.message
        fake_msg.from_user = cb.from_user
        await start_cmd(client, cb.message)
    else:
        await cb.answer("❌ You haven't joined yet! Please join the channel first.", show_alert=True)

@Client.on_callback_query(filters.regex("^back_home$"))
async def back_home_cb(client: Client, cb: CallbackQuery):
    await cb.answer()
    await cb.message.delete()
    await start_cmd(client, cb.message)

@Client.on_callback_query(filters.regex("^help_main$"))
async def help_cb(client: Client, cb: CallbackQuery):
    await cb.answer()
    await send_help(cb.message)

@Client.on_callback_query(filters.regex("^plans_info$"))
async def plans_cb(client: Client, cb: CallbackQuery):
    await cb.answer()
    await show_plans(cb.message)

@Client.on_callback_query(filters.regex("^my_stats$"))
async def my_stats_cb(client: Client, cb: CallbackQuery):
    await cb.answer()
    await mystats_cmd(client, cb.message)

@Client.on_callback_query(filters.regex("^buy_premium$"))
async def buy_premium_cb(client: Client, cb: CallbackQuery):
    await cb.answer()
    await show_plans(cb.message)
