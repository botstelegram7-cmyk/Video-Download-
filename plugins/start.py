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

# ── Try to use pyroblock colored buttons ──────────────────────────────────────
try:
    from pyroblock import enums as pb_enums
    PYROBLOCK = True
    print("[PYROBLOCK] ✅ Colored buttons enabled", flush=True)
except ImportError:
    PYROBLOCK = False
    print("[PYROBLOCK] ℹ️  Not installed — using standard buttons", flush=True)

def _btn(text, cb=None, url=None, style=None):
    """Create InlineKeyboardButton with optional pyroblock style."""
    kwargs = {"callback_data": cb} if cb else {"url": url}
    if PYROBLOCK and style:
        kwargs["style"] = style
    return InlineKeyboardButton(text, **kwargs)

def uptime_str() -> str:
    delta = datetime.now() - BOT_START_TIME
    days    = delta.days
    hours   = delta.seconds // 3600
    minutes = (delta.seconds % 3600) // 60
    return f"{days}d {hours}h {minutes}m"

# ══════════════════════════════════════════════════
#  /start
# ══════════════════════════════════════════════════
@app.on_message(filters.command("start") & filters.incoming)
async def start_cmd(client, message: Message):
    print(f"[START] /start received from user_id={message.from_user.id}", flush=True)
    user = message.from_user

    # Ensure user in DB
    try:
        await db.get_or_create_user(user.id, user.username, user.first_name)
    except Exception as e:
        print(f"[START] DB error: {e}", flush=True)

    # ── Force subscribe check ────────────────────────────────────
    if not is_owner(user.id) and Config.FORCE_SUB_CHANNEL_ID:
        try:
            subscribed = await is_subscribed(client, user.id)
        except Exception as e:
            print(f"[START] sub check error: {e}", flush=True)
            subscribed = True

        if not subscribed:
            if PYROBLOCK:
                btn = InlineKeyboardMarkup([[
                    _btn("📢 Join Channel", url=Config.FORCE_SUB_CHANNEL),
                    _btn("✅ I Joined",     cb="check_sub", style=pb_enums.ButtonStyles.PRIMARY),
                ]])
            else:
                btn = InlineKeyboardMarkup([[
                    InlineKeyboardButton("📢 Join Channel", url=Config.FORCE_SUB_CHANNEL),
                    InlineKeyboardButton("✅ I Joined",     callback_data="check_sub"),
                ]])
            text = (
                "⋆｡° ✮ °｡⋆\n"
                "-ˏˋ⋆ ᴡ ᴇ ʟ ᴄ ᴏ ᴍ ᴇ ⋆ˊˎ-\n\n"
                f"🌸 Hello **{user.first_name}**!\n\n"
                "⚠️ Please join our channel first,\n"
                "then click **✅ I Joined**."
            )
            try:
                if Config.START_PIC:
                    await message.reply_photo(photo=Config.START_PIC, caption=text, reply_markup=btn)
                else:
                    await message.reply(text, reply_markup=btn)
            except Exception as e:
                print(f"[START] force-sub reply error: {e}", flush=True)
            return

    # ── Main start message ────────────────────────────────────────
    try:
        db_user = await db.get_user(user.id)
        plan    = db_user.get("plan", "free") if db_user else "free"
    except Exception as e:
        print(f"[START] get_user error: {e}", flush=True)
        plan = "free"

    await _send_start_message(client, message, user, plan)


async def _send_start_message(client, target_msg, user, plan):
    owner_url   = "https://t.me/" + Config.OWNER_USERNAME.strip("@")
    support_url = "https://t.me/" + Config.OWNER_USERNAME2.strip("@")

    if PYROBLOCK:
        buttons = InlineKeyboardMarkup([
            [
                _btn("📖 Help",     cb="help_main",    style=pb_enums.ButtonStyles.SUCCESS),
                _btn("💎 Plans",    cb="plans_info",   style=pb_enums.ButtonStyles.SUCCESS),
            ],
            [
                _btn("📊 My Stats",    cb="my_stats",    style=pb_enums.ButtonStyles.PRIMARY),
                _btn("📜 History",     cb="my_history",  style=pb_enums.ButtonStyles.PRIMARY),
                _btn("⚙️ Settings",   cb="settings_menu",style=pb_enums.ButtonStyles.PRIMARY),
            ],
            [
                _btn("🔔 Channel", url=Config.FORCE_SUB_CHANNEL),
            ],
            [
                _btn("👑 Owner",   url=owner_url),
                _btn("📞 Support", url=support_url),
            ],
        ])
    else:
        buttons = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("📖 Help",     callback_data="help_main"),
                InlineKeyboardButton("💎 Plans",    callback_data="plans_info"),
            ],
            [
                InlineKeyboardButton("📊 My Stats", callback_data="my_stats"),
                InlineKeyboardButton("📜 History",  callback_data="my_history"),
                InlineKeyboardButton("⚙️ Settings", callback_data="settings_menu"),
            ],
            [
                InlineKeyboardButton("🔔 Channel",  url=Config.FORCE_SUB_CHANNEL),
            ],
            [
                InlineKeyboardButton("👑 Owner",    url=owner_url),
                InlineKeyboardButton("📞 Support",  url=support_url),
            ],
        ])

    caption = (
        "⋆｡° ✮ °｡⋆\n"
        "-ˏˋ⋆ ᴡ ᴇ ʟ ᴄ ᴏ ᴍ ᴇ ⋆ˊˎ-\n\n"
        f"✨ Hello **{user.first_name}**! I am\n"
        f"**{Config.BOT_NAME}**\n\n"
        "»»──── 🌐 Supported Sources ────««\n"
        "▸ 🎥 YouTube — Video / Shorts / Playlist\n"
        "▸ 📸 Instagram — Reels / Posts / Stories\n"
        "▸ 🎵 TikTok / Twitter-X / Facebook\n"
        "▸ 📦 Terabox — Any link\n"
        "▸ 🔗 Google Drive — Any file\n"
        "▸ 🌊 M3U8 / HLS Streams\n"
        "▸ 🔗 Direct Links — .mp4 .apk .zip .rar etc\n"
        "▸ 📄 .txt files with multiple links\n"
        "▸ 🌐 1000+ sites via yt-dlp\n\n"
        "»»──── 🎯 Extra Features ────««\n"
        "▸ 🎵 /audio — Audio-only download\n"
        "▸ ℹ️  /info  — URL info (no download)\n"
        "▸ 📋 /history — Your download history\n"
        "▸ ⏱  Real-time progress bars\n"
        "▸ 🖼️  Auto thumbnail + metadata\n\n"
        f"🏷️  Your Plan : **{plan_badge(plan)}**\n"
        "⋆ ｡˚ Send any link to download! ˚｡ ⋆\n\n"
        "»»────── " + Config.DIVIDER_SM + " ──────««"
    )

    try:
        if Config.START_PIC:
            await target_msg.reply_photo(photo=Config.START_PIC, caption=caption, reply_markup=buttons)
        else:
            await target_msg.reply(caption, reply_markup=buttons)
        print("[START] Start message sent successfully", flush=True)
    except Exception as e:
        print(f"[START] reply_photo failed: {e}, trying plain reply", flush=True)
        try:
            await target_msg.reply(caption, reply_markup=buttons)
        except Exception as e2:
            print(f"[START] plain reply also failed: {e2}", flush=True)


# ══════════════════════════════════════════════════
#  /help
# ══════════════════════════════════════════════════
@app.on_message(filters.command("help") & filters.incoming)
async def help_cmd(client, message: Message):
    print(f"[HELP] from {message.from_user.id}", flush=True)
    await _send_help(message)

async def _send_help(target):
    text = (
        "»»────── 📖 HELP MENU ──────««\n\n"
        "⋆｡° ✮ **HOW TO USE** ✮ °｡⋆\n\n"
        "Just send any **link** — I'll download it!\n\n"
        "»»────── 📥 Supported ──────««\n"
        "🎥  YouTube — video / shorts / playlist\n"
        "📸  Instagram — reels / posts / stories\n"
        "🎵  TikTok / Twitter-X / Facebook\n"
        "📦  Terabox — any link\n"
        "🔗  Google Drive — any file\n"
        "🌊  M3U8 / HLS streams\n"
        "🔗  Direct links (.mp4 .zip .apk .rar…)\n"
        "📄  .txt files with multiple links\n"
        "🌐  1000+ sites via yt-dlp\n\n"
        "»»────── ⌨️ Commands ──────««\n"
        "/start     — Welcome menu\n"
        "/help      — This menu\n"
        "/audio URL — Download audio only 🎵\n"
        "/info URL  — Get info without downloading\n"
        "/history   — Your download history\n"
        "/mystats   — Your stats & quota\n"
        "/queue     — Active downloads\n"
        "/cancel    — Cancel downloads\n"
        "/status    — Bot status & uptime\n"
        "/plans     — Pricing plans\n"
        "/ping      — Check response time\n"
        "/feedback  — Send feedback\n\n"
        "»»────── 👑 Admin ──────««\n"
        "/givepremium [id] [plan]\n"
        "/removepremium [id]\n"
        "/ban [id]  |  /unban [id]\n"
        "/broadcast [msg]\n"
        "/stats  |  /users  |  /banned\n"
        "/restart\n\n"
        "»»──────────────────────────««\n"
        f"⋆ ｡˚ Owned by {Config.OWNER_USERNAME} ˚｡ ⋆"
    )
    if PYROBLOCK:
        btn = InlineKeyboardMarkup([[
            _btn("🏠 Home", cb="back_home",  style=pb_enums.ButtonStyles.SUCCESS),
            _btn("💎 Plans", cb="plans_info", style=pb_enums.ButtonStyles.PRIMARY),
        ]])
    else:
        btn = InlineKeyboardMarkup([[
            InlineKeyboardButton("🏠 Home",  callback_data="back_home"),
            InlineKeyboardButton("💎 Plans", callback_data="plans_info"),
        ]])

    is_msg = isinstance(target, Message)
    if is_msg:
        await target.reply(text, reply_markup=btn, quote=True)
    else:
        try: await target.message.edit_text(text, reply_markup=btn)
        except: await target.message.reply(text, reply_markup=btn)


# ══════════════════════════════════════════════════
#  /ping
# ══════════════════════════════════════════════════
@app.on_message(filters.command("ping") & filters.incoming)
async def ping_cmd(client, message: Message):
    import time
    start = time.time()
    sent  = await message.reply("🏓 Pong!", quote=True)
    ms    = int((time.time() - start) * 1000)
    await sent.edit_text(
        "»»──── 🏓 PONG ────««\n\n"
        f"  ⚡ Response : **{ms} ms**\n"
        f"  ⏰ Uptime   : **{uptime_str()}**\n\n"
        "»»──────────────────««"
    )


# ══════════════════════════════════════════════════
#  /status
# ══════════════════════════════════════════════════
@app.on_message(filters.command("status") & filters.incoming)
async def status_cmd(client, message: Message):
    try:
        total_users = await db.get_total_users()
        total_dls   = await db.get_total_downloads()
        me          = await client.get_me()
        text = (
            "»»────── 📊 BOT STATUS ──────««\n\n"
            f"🤖 Bot     : @{me.username}\n"
            f"⏰ Uptime  : **{uptime_str()}**\n"
            f"👥 Users   : **{total_users}**\n"
            f"📥 Done DLs: **{total_dls}**\n\n"
            "⋆ ｡˚ Everything running smoothly! ˚｡ ⋆\n\n"
            "»»──────────────────────────««"
        )
    except Exception as e:
        text = f"»»──── 📊 STATUS ────««\n\n⏰ Uptime: **{uptime_str()}**\n\nError: {e}"
    await message.reply(text, quote=True)


# ══════════════════════════════════════════════════
#  /plans  /buy
# ══════════════════════════════════════════════════
@app.on_message(filters.command(["plans", "buy"]) & filters.incoming)
async def plans_cmd(client, message: Message):
    await _send_plans(message)

async def _send_plans(target):
    text = (
        "»»────── 💎 PLANS & PRICING ──────««\n\n"
        "🆓 **Free Plan**\n"
        f"   ▸ {Config.FREE_DAILY_LIMIT} downloads / day\n\n"
        "🥉 **Basic Plan** — _1 Month_\n"
        f"   ▸ {Config.BASIC_DAILY_LIMIT} downloads / day\n"
        "   ▸ All sites + Terabox + GDrive\n"
        "   ▸ Priority queue\n\n"
        "💎 **Premium Plan** — _1 Year_\n"
        f"   ▸ {Config.PREMIUM_DAILY_LIMIT} downloads / day\n"
        "   ▸ All features + VIP support\n"
        "   ▸ Highest priority\n\n"
        "»»────── 💳 HOW TO BUY ──────««\n"
        "  1️⃣  Contact owner / support\n"
        "  2️⃣  Pay via UPI / QR / Crypto\n"
        "  3️⃣  Send payment screenshot\n"
        "  4️⃣  Plan activated instantly! 🎉\n\n"
        "»»──────────────────────────────««"
    )
    owner_url   = "https://t.me/" + Config.OWNER_USERNAME.strip("@")
    support_url = "https://t.me/" + Config.OWNER_USERNAME2.strip("@")
    if PYROBLOCK:
        btn = InlineKeyboardMarkup([
            [
                _btn("👑 Owner",    url=owner_url),
                _btn("📞 Support",  url=support_url),
            ],
            [_btn("🏠 Back", cb="back_home", style=pb_enums.ButtonStyles.DANGER)]
        ])
    else:
        btn = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("👑 Owner",   url=owner_url),
                InlineKeyboardButton("📞 Support", url=support_url),
            ],
            [InlineKeyboardButton("🏠 Back", callback_data="back_home")]
        ])
    is_msg = isinstance(target, Message)
    if is_msg:
        await target.reply(text, reply_markup=btn, quote=True)
    else:
        try: await target.message.edit_text(text, reply_markup=btn)
        except: await target.message.reply(text, reply_markup=btn)


# ══════════════════════════════════════════════════
#  /mystats
# ══════════════════════════════════════════════════
@app.on_message(filters.command("mystats") & filters.incoming)
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
        bar_len   = 10
        filled    = int((used / limit) * bar_len) if limit > 0 else 0
        usage_bar = "🟩" * filled + "⬜" * (bar_len - filled)
        text = (
            "»»────── 👤 MY STATS ──────««\n\n"
            f"🆔 ID      : `{user_id}`\n"
            f"🏷️  Plan    : **{plan_badge(plan)}**\n"
            f"📅 Expires : **{expiry}**\n"
            f"🗓️  Joined  : **{joined}**\n\n"
            "»»────── 📊 Today's Usage ──────««\n"
            f"  {usage_bar}\n"
            f"  📥 {used} / {limit} downloads used\n\n"
            "»»──────────────────────────««"
        )
        if PYROBLOCK:
            btn = InlineKeyboardMarkup([[
                _btn("💎 Upgrade",  cb="plans_info",  style=pb_enums.ButtonStyles.SUCCESS),
                _btn("📜 History",  cb="my_history",  style=pb_enums.ButtonStyles.PRIMARY),
                _btn("🏠 Home",     cb="back_home",   style=pb_enums.ButtonStyles.DANGER),
            ]])
        else:
            btn = InlineKeyboardMarkup([[
                InlineKeyboardButton("💎 Upgrade", callback_data="plans_info"),
                InlineKeyboardButton("📜 History", callback_data="my_history"),
                InlineKeyboardButton("🏠 Home",    callback_data="back_home"),
            ]])
        await message.reply(text, reply_markup=btn, quote=True)
    except Exception as e:
        print(f"[MYSTATS] error: {e}", flush=True)
        await message.reply("Could not fetch stats. Try again.", quote=True)


# ══════════════════════════════════════════════════
#  /history
# ══════════════════════════════════════════════════
@app.on_message(filters.command("history") & filters.incoming)
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
        print(f"[HISTORY] error: {e}", flush=True)
        await message.reply("Could not fetch history.", quote=True)


# ══════════════════════════════════════════════════
#  /feedback
# ══════════════════════════════════════════════════
@app.on_message(filters.command("feedback") & filters.incoming)
async def feedback_cmd(client, message: Message):
    user = message.from_user
    args = message.text.split(None, 1)
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
    except: pass
    owner_id = Config.OWNER_IDS[0] if Config.OWNER_IDS else None
    if owner_id:
        try:
            await client.send_message(
                owner_id,
                "»»──── 💬 NEW FEEDBACK ────««\n\n"
                f"👤 From: {user.first_name} (@{user.username or '?'}) | `{user.id}`\n\n"
                f"📝 Message:\n{feedback_text}\n\n"
                "»»──────────────────────────««"
            )
        except: pass
    await message.reply(
        "»»──── ✅ FEEDBACK SENT ────««\n\n"
        "Thanks! Sent to the owner. 💖",
        quote=True
    )


# ══════════════════════════════════════════════════
#  /settings
# ══════════════════════════════════════════════════
@app.on_message(filters.command("settings") & filters.incoming)
async def settings_cmd(client, message: Message):
    uid  = message.from_user.id
    user = await db.get_user(uid)
    plan = user.get("plan", "free") if user else "free"
    if PYROBLOCK:
        btn = InlineKeyboardMarkup([
            [_btn("💎 Upgrade",    cb="plans_info",   style=pb_enums.ButtonStyles.SUCCESS)],
            [_btn("📊 My Stats",  cb="my_stats",      style=pb_enums.ButtonStyles.PRIMARY),
             _btn("📜 History",   cb="my_history",    style=pb_enums.ButtonStyles.PRIMARY)],
            [_btn("🏠 Home",      cb="back_home",     style=pb_enums.ButtonStyles.DANGER)],
        ])
    else:
        btn = InlineKeyboardMarkup([
            [InlineKeyboardButton("💎 Upgrade",  callback_data="plans_info")],
            [InlineKeyboardButton("📊 My Stats", callback_data="my_stats"),
             InlineKeyboardButton("📜 History",  callback_data="my_history")],
            [InlineKeyboardButton("🏠 Home",     callback_data="back_home")],
        ])
    await message.reply(
        "»»──── ⚙️ SETTINGS ────««\n\n"
        f"🏷️  Plan    : **{plan_badge(plan)}**\n"
        f"🆔 User ID : `{uid}`\n\n"
        "»»──────────────────────««",
        reply_markup=btn, quote=True
    )


# ══════════════════════════════════════════════════
#  CALLBACK QUERIES
# ══════════════════════════════════════════════════
@app.on_callback_query(filters.regex("^check_sub$"))
async def check_sub_cb(client, cb: CallbackQuery):
    uid = cb.from_user.id
    try:
        subscribed = await is_subscribed(client, uid)
    except:
        subscribed = True

    if subscribed:
        await cb.answer("✅ Verified! Welcome!", show_alert=True)
        try: await cb.message.delete()
        except: pass
        try:
            db_user = await db.get_user(uid)
            plan    = db_user.get("plan", "free") if db_user else "free"
            await _send_start_message(client, cb.message, cb.from_user, plan)
        except Exception as e:
            print(f"[check_sub] post-join start error: {e}", flush=True)
    else:
        await cb.answer("❌ Please join the channel first!", show_alert=True)

@app.on_callback_query(filters.regex("^back_home$"))
async def back_home_cb(client, cb: CallbackQuery):
    await cb.answer()
    try: await cb.message.delete()
    except: pass
    try:
        db_user = await db.get_user(cb.from_user.id)
        plan    = db_user.get("plan", "free") if db_user else "free"
        await _send_start_message(client, cb.message, cb.from_user, plan)
    except Exception as e:
        print(f"[back_home] error: {e}", flush=True)

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
    if PYROBLOCK:
        btn = InlineKeyboardMarkup([
            [_btn("💎 Upgrade",  cb="plans_info",  style=pb_enums.ButtonStyles.SUCCESS)],
            [_btn("📊 Stats",   cb="my_stats",    style=pb_enums.ButtonStyles.PRIMARY),
             _btn("📜 History", cb="my_history",  style=pb_enums.ButtonStyles.PRIMARY)],
            [_btn("🏠 Home",    cb="back_home",   style=pb_enums.ButtonStyles.DANGER)],
        ])
    else:
        btn = InlineKeyboardMarkup([
            [InlineKeyboardButton("💎 Upgrade",  callback_data="plans_info")],
            [InlineKeyboardButton("📊 Stats",    callback_data="my_stats"),
             InlineKeyboardButton("📜 History",  callback_data="my_history")],
            [InlineKeyboardButton("🏠 Home",     callback_data="back_home")],
        ])
    try:
        await cb.message.edit_text(
            "»»──── ⚙️ SETTINGS ────««\n\n"
            f"🏷️  Plan    : **{plan_badge(plan)}**\n"
            f"🆔 User ID : `{uid}`\n\n"
            "»»──────────────────────««",
            reply_markup=btn
        )
    except: pass
