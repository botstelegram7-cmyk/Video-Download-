"""
╔══════════════════════════════════════════════════════════╗
║   🚀  START · HELP · PLANS · STATS · CALLBACKS          ║
║   Owner : @Xioqui_Xan   Support : @TechnicalSerena      ║
╚══════════════════════════════════════════════════════════╝
"""
import logging
from datetime import datetime
from pyrogram import filters
from pyrogram.types import (
    Message, CallbackQuery,
    InlineKeyboardMarkup, InlineKeyboardButton as Btn
)
from client import app
from config import Config
import database as db
from utils.helpers import is_owner, is_subbed, plan_badge

log        = logging.getLogger(__name__)
_BOOT_TIME = datetime.now()

def uptime() -> str:
    d = datetime.now() - _BOOT_TIME
    h, r = divmod(d.seconds, 3600); m, s = divmod(r, 60)
    return f"{d.days}d {h}h {m}m"

# ── Keyboard builders ────────────────────────────────────
def _home_kb() -> InlineKeyboardMarkup:
    o = f"https://t.me/{Config.OWNER_UNAME}"
    s = f"https://t.me/{Config.SUPPORT_UNAME}"
    return InlineKeyboardMarkup([
        [Btn("📖 Help",      callback_data="help"),
         Btn("💎 Plans",     callback_data="plans")],
        [Btn("📊 My Stats",  callback_data="stats"),
         Btn("📜 History",   callback_data="history"),
         Btn("⚙️ Settings",  callback_data="settings")],
        [Btn("🔔 Channel",   url=Config.FSUB_LINK)],
        [Btn("👑 Owner",     url=o),
         Btn("📞 Support",   url=s)],
    ])

def _back_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([[Btn("🏠 Home", callback_data="home")]])

# ═══════════════════════════════════════════════════════
#  /start
# ═══════════════════════════════════════════════════════
@app.on_message(filters.command("start") & filters.incoming)
async def cmd_start(client, msg: Message):
    u = msg.from_user
    log.info("/start uid=%s", u.id)

    # Register user
    try:
        await db.ensure_user(u.id, u.username or "", u.first_name or "")
    except Exception as e:
        log.error("ensure_user: %s", e)

    # Force-sub
    if not is_owner(u.id) and Config.FSUB_ID:
        if not await is_subbed(client, u.id):
            txt = (
                "⋆｡° ✮ °｡⋆\n"
                "-ˏˋ⋆ ᴡ ᴇ ʟ ᴄ ᴏ ᴍ ᴇ ⋆ˊˎ-\n\n"
                f"🌸 Hello **{u.first_name}**!\n\n"
                "⚠️ Join our channel to use this bot.\n"
                "Then tap **✅ Joined** below."
            )
            kb = InlineKeyboardMarkup([[
                Btn("📢 Join Channel", url=Config.FSUB_LINK),
                Btn("✅ Joined",        callback_data="check_sub"),
            ]])
            try:
                if Config.START_PIC:
                    await msg.reply_photo(Config.START_PIC, caption=txt, reply_markup=kb)
                else:
                    await msg.reply(txt, reply_markup=kb)
            except Exception as e:
                log.error("start force-sub: %s", e)
            return

    await _send_home(msg, u)

async def _send_home(target, user):
    """Send welcome message. target = Message or stub with .reply()."""
    db_u = await db.get_user(user.id)
    plan = db_u.get("plan","free") if db_u else "free"
    txt  = (
        "⋆｡° ✮ °｡⋆\n"
        "-ˏˋ⋆ ᴡ ᴇ ʟ ᴄ ᴏ ᴍ ᴇ ⋆ˊˎ-\n\n"
        f"✨ Hello **{user.first_name}**!  I'm\n"
        f"**{Config.BOT_NAME}**\n\n"
        "»»──── 🌐 What I Can Download ────««\n"
        "▸ 🎥 YouTube — Video / Shorts / Playlist\n"
        "▸ 📸 Instagram — Reels / Posts / Stories\n"
        "▸ 🎵 TikTok / Twitter-X / Facebook\n"
        "▸ 📦 Terabox — Any link\n"
        "▸ 🔗 Google Drive — Any file\n"
        "▸ 🌊 M3U8 / HLS Streams\n"
        "▸ 🔗 Direct Links — .mp4 .apk .zip .rar…\n"
        "▸ 📄 .txt file with multiple links\n"
        "▸ 🌐 1000+ sites via yt-dlp\n\n"
        "»»──── ✨ Features ────««\n"
        "▸ 🎵 Audio-only mode — /audio\n"
        "▸ ℹ️  URL info — /info\n"
        "▸ 📋 Download history — /history\n"
        "▸ ⏱  Real-time progress bars\n"
        "▸ 🖼️  Auto thumbnail & metadata\n"
        "▸ 🗂️  Original extension preserved\n\n"
        f"🏷️  **Your Plan : {plan_badge(plan)}**\n\n"
        "⋆ ｡˚ Send any link to start! ˚｡ ⋆"
    )
    try:
        if Config.START_PIC:
            await target.reply_photo(Config.START_PIC, caption=txt, reply_markup=_home_kb())
        else:
            await target.reply(txt, reply_markup=_home_kb())
    except Exception as e:
        log.error("_send_home: %s", e)
        try: await target.reply(txt, reply_markup=_home_kb())
        except: pass

# ═══════════════════════════════════════════════════════
#  /help
# ═══════════════════════════════════════════════════════
@app.on_message(filters.command("help") & filters.incoming)
async def cmd_help(client, msg: Message):
    await _help_text(msg)

async def _help_text(target):
    txt = (
        "»»──────── 📖 HELP MENU ────────««\n\n"
        "⋆｡° ✮  HOW TO USE  ✮ °｡⋆\n\n"
        "Just send any **link** and I'll download it!\n\n"
        "»»──── 📥 Supported Sources ────««\n"
        "🎥  YouTube — video / shorts / playlist\n"
        "📸  Instagram — reels / posts / stories\n"
        "🎵  TikTok / Twitter-X / Facebook\n"
        "📦  Terabox — any link\n"
        "🔗  Google Drive — any file\n"
        "🌊  M3U8 / HLS streams\n"
        "🔗  Direct links (.mp4 .zip .apk .rar…)\n"
        "📄  .txt file with multiple links\n"
        "🌐  1000+ sites via yt-dlp\n\n"
        "»»──── ⌨️ User Commands ────««\n"
        "/start      — Welcome menu\n"
        "/help       — This menu\n"
        "/audio URL  — Download audio only 🎵\n"
        "/info URL   — Get info without downloading\n"
        "/history    — Your download history\n"
        "/mystats    — Your stats & quota\n"
        "/queue      — Active downloads\n"
        "/cancel     — Cancel your downloads\n"
        "/status     — Bot status\n"
        "/plans      — Pricing plans\n"
        "/ping       — Check response time\n"
        "/feedback   — Send feedback\n\n"
        "»»──── 👑 Admin Commands ────««\n"
        "/givepremium [id] [plan]\n"
        "/removepremium [id]\n"
        "/ban [id]  /unban [id]\n"
        "/broadcast [msg]\n"
        "/stats  /users  /banned\n"
        "/restart\n\n"
        "»»──────────────────────────────««\n"
        f"⋆ ｡˚  Owned by @{Config.OWNER_UNAME}  ˚｡ ⋆"
    )
    is_msg = isinstance(target, Message)
    if is_msg:
        await target.reply(txt, reply_markup=_back_kb(), quote=True)
    else:
        try:   await target.message.edit_text(txt, reply_markup=_back_kb())
        except: await target.message.reply(txt, reply_markup=_back_kb())

# ═══════════════════════════════════════════════════════
#  /ping
# ═══════════════════════════════════════════════════════
@app.on_message(filters.command("ping") & filters.incoming)
async def cmd_ping(client, msg: Message):
    import time
    t   = time.time()
    m   = await msg.reply("🏓 Pong!", quote=True)
    ms  = int((time.time() - t) * 1000)
    await m.edit_text(
        "»»──── 🏓 PONG ────««\n\n"
        f"  ⚡ Response : **{ms} ms**\n"
        f"  ⏰ Uptime   : **{uptime()}**\n\n"
        "»»──────────────────««"
    )

# ═══════════════════════════════════════════════════════
#  /status
# ═══════════════════════════════════════════════════════
@app.on_message(filters.command("status") & filters.incoming)
async def cmd_status(client, msg: Message):
    try:
        users = await db.total_users()
        dls   = await db.total_downloads()
        me    = await client.get_me()
        txt   = (
            "»»────── 📊 BOT STATUS ──────««\n\n"
            f"🤖 Bot     : @{me.username}\n"
            f"⏰ Uptime  : **{uptime()}**\n"
            f"👥 Users   : **{users}**\n"
            f"📥 Done DLs: **{dls}**\n\n"
            "⋆ ｡˚ Running smoothly! ˚｡ ⋆\n\n"
            "»»──────────────────────────««"
        )
    except Exception as e:
        txt = f"»»──── 📊 STATUS ────««\n\n⏰ {uptime()}\n\nError: {e}"
    await msg.reply(txt, quote=True)

# ═══════════════════════════════════════════════════════
#  /plans  /buy
# ═══════════════════════════════════════════════════════
@app.on_message(filters.command(["plans","buy"]) & filters.incoming)
async def cmd_plans(client, msg: Message):
    await _plans_text(msg)

async def _plans_text(target):
    o = f"https://t.me/{Config.OWNER_UNAME}"
    s = f"https://t.me/{Config.SUPPORT_UNAME}"
    txt = (
        "»»────── 💎 PLANS & PRICING ──────««\n\n"
        "🆓 **Free Plan**\n"
        f"   ▸ {Config.FREE_LIMIT} downloads / day\n\n"
        "🥉 **Basic Plan** — _1 Month_\n"
        f"   ▸ {Config.BASIC_LIMIT} downloads / day\n"
        "   ▸ All sites + Terabox + GDrive\n"
        "   ▸ Priority queue\n\n"
        "💎 **Premium Plan** — _1 Year_\n"
        f"   ▸ {Config.PREMIUM_LIMIT} downloads / day\n"
        "   ▸ All features + VIP support\n"
        "   ▸ Highest priority\n\n"
        "»»────── 💳 HOW TO BUY ──────««\n"
        "  1️⃣  Contact owner / support\n"
        "  2️⃣  Pay via UPI / QR / Crypto\n"
        "  3️⃣  Send payment screenshot\n"
        "  4️⃣  Plan activated instantly! 🎉\n\n"
        "»»──────────────────────────────««"
    )
    kb = InlineKeyboardMarkup([
        [Btn("👑 Owner",   url=o), Btn("📞 Support", url=s)],
        [Btn("🏠 Home", callback_data="home")],
    ])
    is_msg = isinstance(target, Message)
    if is_msg:
        await target.reply(txt, reply_markup=kb, quote=True)
    else:
        try:   await target.message.edit_text(txt, reply_markup=kb)
        except: await target.message.reply(txt, reply_markup=kb)

# ═══════════════════════════════════════════════════════
#  /mystats
# ═══════════════════════════════════════════════════════
@app.on_message(filters.command("mystats") & filters.incoming)
async def cmd_mystats(client, msg: Message):
    await _stats_text(msg, msg.from_user.id)

async def _stats_text(target, uid: int):
    try:
        user = await db.reset_if_new_day(uid)
        if not user:
            if isinstance(target, Message):
                await target.reply("Please /start first.", quote=True)
            return
        used, lim  = await db.get_limit(user)
        plan       = user.get("plan","free")
        expiry     = (user.get("plan_expiry") or "")[:10] or "—"
        joined     = (user.get("joined_at")   or "")[:10] or "—"
        bar_filled = int((used / lim) * 10) if lim else 0
        bar        = "🟩" * bar_filled + "⬜" * (10 - bar_filled)
        txt = (
            "»»────── 👤 MY STATS ──────««\n\n"
            f"🆔 ID      : `{uid}`\n"
            f"🏷️  Plan    : **{plan_badge(plan)}**\n"
            f"📅 Expires : **{expiry}**\n"
            f"🗓️  Joined  : **{joined}**\n\n"
            "»»────── 📊 Today's Quota ──────««\n"
            f"  {bar}\n"
            f"  📥 {used} / {lim} downloads used\n\n"
            "»»──────────────────────────««"
        )
        kb = InlineKeyboardMarkup([
            [Btn("💎 Upgrade", callback_data="plans"),
             Btn("📜 History", callback_data="history"),
             Btn("🏠 Home",    callback_data="home")],
        ])
        if isinstance(target, Message):
            await target.reply(txt, reply_markup=kb, quote=True)
        else:
            try:   await target.edit_text(txt, reply_markup=kb)
            except: await target.reply(txt, reply_markup=kb)
    except Exception as e:
        log.error("_stats_text: %s", e)

# ═══════════════════════════════════════════════════════
#  /history
# ═══════════════════════════════════════════════════════
@app.on_message(filters.command("history") & filters.incoming)
async def cmd_history(client, msg: Message):
    await _history_text(msg, msg.from_user.id)

async def _history_text(target, uid: int):
    try:
        dls = await db.get_history(uid, 10)
        if not dls:
            txt = ("»»────── 📜 HISTORY ──────««\n\n"
                   "No downloads yet! Send a link to start.\n\n"
                   "»»──────────────────────────««")
        else:
            lines = ["»»────── 📜 DOWNLOAD HISTORY ──────««\n"]
            for i, d in enumerate(dls, 1):
                name = (d.get("title") or "Unknown")[:35]
                date = (d.get("created_at") or "")[:10]
                lines.append(f"  {i}. 📄 `{name}`\n     📅 {date}")
            lines.append("\n»»──────────────────────────────««")
            txt = "\n".join(lines)
        if isinstance(target, Message):
            await target.reply(txt, reply_markup=_back_kb(), quote=True)
        else:
            try:   await target.edit_text(txt, reply_markup=_back_kb())
            except: await target.reply(txt, reply_markup=_back_kb())
    except Exception as e:
        log.error("_history_text: %s", e)

# ═══════════════════════════════════════════════════════
#  /settings
# ═══════════════════════════════════════════════════════
@app.on_message(filters.command("settings") & filters.incoming)
async def cmd_settings(client, msg: Message):
    await _settings_text(msg, msg.from_user.id)

async def _settings_text(target, uid: int):
    u    = await db.get_user(uid)
    plan = u.get("plan","free") if u else "free"
    txt  = (
        "»»──── ⚙️ SETTINGS ────««\n\n"
        f"🆔 User ID : `{uid}`\n"
        f"🏷️  Plan    : **{plan_badge(plan)}**\n\n"
        "»»──────────────────────««"
    )
    kb = InlineKeyboardMarkup([
        [Btn("💎 Upgrade",  callback_data="plans"),
         Btn("📊 Stats",    callback_data="stats")],
        [Btn("📜 History",  callback_data="history")],
        [Btn("🏠 Home",     callback_data="home")],
    ])
    if isinstance(target, Message):
        await target.reply(txt, reply_markup=kb, quote=True)
    else:
        try:   await target.edit_text(txt, reply_markup=kb)
        except: await target.reply(txt, reply_markup=kb)

# ═══════════════════════════════════════════════════════
#  /feedback
# ═══════════════════════════════════════════════════════
@app.on_message(filters.command("feedback") & filters.incoming)
async def cmd_feedback(client, msg: Message):
    u    = msg.from_user
    args = msg.text.split(None, 1)
    if len(args) < 2:
        await msg.reply(
            "»»──── 💬 FEEDBACK ────««\n\n"
            "Usage: `/feedback Your message here`\n\n"
            "»»──────────────────────────««",
            quote=True
        )
        return
    text = args[1].strip()
    try: await db.save_feedback(u.id, text)
    except: pass
    if Config.OWNER_IDS:
        try:
            await client.send_message(
                Config.OWNER_IDS[0],
                "»»──── 💬 FEEDBACK ────««\n\n"
                f"👤 {u.first_name} (@{u.username or '?'}) `{u.id}`\n\n"
                f"📝 {text}\n\n"
                "»»──────────────────────────««"
            )
        except: pass
    await msg.reply(
        "»»──── ✅ Feedback Sent ────««\n\n"
        "Thank you! Owner has been notified. 💖",
        quote=True
    )

# ═══════════════════════════════════════════════════════
#  CALLBACKS
# ═══════════════════════════════════════════════════════
@app.on_callback_query(filters.regex("^check_sub$"))
async def cb_check_sub(client, cb: CallbackQuery):
    uid = cb.from_user.id
    try:   ok = await is_subbed(client, uid)
    except: ok = True
    if ok:
        await cb.answer("✅ Verified! Welcome!", show_alert=True)
        try: await cb.message.delete()
        except: pass
        try:
            u = await db.get_user(uid)
            await _send_home(cb.message, cb.from_user)
        except Exception as e:
            log.error("cb check_sub post: %s", e)
    else:
        await cb.answer("❌ Please join the channel first!", show_alert=True)

@app.on_callback_query(filters.regex("^home$"))
async def cb_home(client, cb: CallbackQuery):
    await cb.answer()
    try: await cb.message.delete()
    except: pass
    await _send_home(cb.message, cb.from_user)

@app.on_callback_query(filters.regex("^help$"))
async def cb_help(client, cb: CallbackQuery):
    await cb.answer()
    await _help_text(cb)

@app.on_callback_query(filters.regex("^plans$"))
async def cb_plans(client, cb: CallbackQuery):
    await cb.answer()
    await _plans_text(cb)

@app.on_callback_query(filters.regex("^stats$"))
async def cb_stats(client, cb: CallbackQuery):
    await cb.answer()
    await _stats_text(cb.message, cb.from_user.id)

@app.on_callback_query(filters.regex("^history$"))
async def cb_history(client, cb: CallbackQuery):
    await cb.answer()
    await _history_text(cb.message, cb.from_user.id)

@app.on_callback_query(filters.regex("^settings$"))
async def cb_settings(client, cb: CallbackQuery):
    await cb.answer()
    await _settings_text(cb.message, cb.from_user.id)
