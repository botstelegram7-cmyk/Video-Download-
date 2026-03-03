from pyrogram import Client, filters
from pyrogram.types import (InlineKeyboardMarkup, InlineKeyboardButton,
                             CallbackQuery, Message)
from client import app
import database as db
from utils.helpers import is_owner, fmt_dt, fmt_size
from utils.decorators import guard
from config import (OWNER_USERNAME, SUPPORT_USERNAME, FSUB_LINK,
                    FREE_LIMIT, BASIC_LIMIT, PREMIUM_LIMIT, START_PIC)
import time, asyncio

START_TIME = time.time()

# ── /start ───────────────────────────────────────────────────────────────────
@app.on_message(filters.command("start") & ~filters.outgoing)
async def cmd_start(client: Client, msg: Message):
    uid  = msg.from_user.id
    fn   = (msg.from_user.first_name or "") + " " + (msg.from_user.last_name or "")
    await db.upsert_user(uid, msg.from_user.username or "", fn.strip())
    user = await db.get_user(uid)
    plan  = user.get("plan", "free") if user else "free"
    badge = {"basic": "🥉", "premium": "💎", "free": "🆓"}.get(plan, "🆓")

    text = (
        f"⋆｡° ✮ °｡⋆\n"
        f"-ˏˋ⋆ ᴡ ᴇ ʟ ᴄ ᴏ ᴍ ᴇ ⋆ˊˎ-\n\n"
        f"»»──── 𝗦𝗲𝗿𝗲𝗻𝗮 𝗗𝗼𝘄𝗻𝗹𝗼𝗮𝗱𝗲𝗿 𝗕𝗼𝘁 ────««\n\n"
        f"▸ Hello, {msg.from_user.first_name or 'there'}!\n"
        f"▸ Plan   : {badge} {plan.capitalize()}\n"
        f"▸ Just send me any URL to download!\n\n"
        f"Supports YouTube, Instagram, TikTok, Twitter,\n"
        f"Facebook, Google Drive, Terabox & 1000+ more!\n\n"
        f"⋆ ｡˚ @{SUPPORT_USERNAME} ˚｡ ⋆"
    )

    kbd = InlineKeyboardMarkup([
        [InlineKeyboardButton("📋 Help",   callback_data="help"),
         InlineKeyboardButton("💼 Plans",  callback_data="plans")],
        [InlineKeyboardButton("📊 Stats",  callback_data="stats"),
         InlineKeyboardButton("⚙️ Settings", callback_data="settings")],
        [InlineKeyboardButton("📢 Support Channel", url=FSUB_LINK)],
    ])

    if START_PIC:
        await msg.reply_photo(START_PIC, caption=text, reply_markup=kbd)
    else:
        await msg.reply(text, reply_markup=kbd)


# ── /help ────────────────────────────────────────────────────────────────────
@app.on_message(filters.command("help") & ~filters.outgoing)
async def cmd_help(client, msg: Message):
    await msg.reply(
        "»»──── 📖 Help Menu ────««\n\n"
        "▸ Send any URL to download media\n"
        "▸ /audio <url>   — Download as MP3\n"
        "▸ /info <url>    — Get media info\n"
        "▸ /mystats       — Your daily stats\n"
        "▸ /history       — Last 10 downloads\n"
        "▸ /queue         — Your active queue\n"
        "▸ /cancel        — Cancel all queued\n"
        "▸ /status        — Bot uptime & stats\n"
        "▸ /plans         — View plans\n"
        "▸ /ping          — Bot response time\n"
        "▸ /feedback msg  — Send feedback\n"
        "▸ /settings      — Your settings\n\n"
        "⋆ ｡˚ Upload a .txt file with URLs to bulk download ˚｡ ⋆\n\n"
        "⋆｡° ✮ @Universal_DownloadBot ✮ °｡⋆"
    )


# ── /ping ────────────────────────────────────────────────────────────────────
@app.on_message(filters.command("ping") & ~filters.outgoing)
async def cmd_ping(client, msg: Message):
    t = time.time()
    m = await msg.reply("Pinging…")
    ms = int((time.time() - t) * 1000)
    await m.edit(f"»»──── 🏓 Pong! ────««\n\n▸ Response: {ms}ms\n\n⋆｡° ✮ @Universal_DownloadBot ✮ °｡⋆")


# ── /status ──────────────────────────────────────────────────────────────────
@app.on_message(filters.command("status") & ~filters.outgoing)
async def cmd_status(client, msg: Message):
    st   = await db.get_stats()
    up_s = int(time.time() - START_TIME)
    m, s = divmod(up_s, 60); h, m = divmod(m, 60)
    await msg.reply(
        f"»»──── 🤖 Bot Status ────««\n\n"
        f"▸ Uptime     : {h}h {m}m {s}s\n"
        f"▸ Users      : {st['total_users']}\n"
        f"▸ Downloads  : {st['total_downloads']}\n"
        f"▸ Premium    : {st['premium_users']}\n"
        f"▸ Banned     : {st['banned_users']}\n\n"
        f"⋆｡° ✮ @Universal_DownloadBot ✮ °｡⋆"
    )


# ── /plans ───────────────────────────────────────────────────────────────────
@app.on_message(filters.command("plans") & ~filters.outgoing)
async def cmd_plans(client, msg: Message):
    await msg.reply(
        f"»»──── 💼 Plans ────««\n\n"
        f"🆓 Free\n  ▸ {FREE_LIMIT} downloads/day — Forever Free\n\n"
        f"🥉 Basic\n  ▸ {BASIC_LIMIT} downloads/day — 30 days\n  ▸ Contact @{OWNER_USERNAME}\n\n"
        f"💎 Premium\n  ▸ {PREMIUM_LIMIT} downloads/day — 365 days\n  ▸ Contact @{OWNER_USERNAME}\n\n"
        f"👑 Owner\n  ▸ Unlimited — Forever\n\n"
        f"⋆ ｡˚ DM @{OWNER_USERNAME} to upgrade ˚｡ ⋆\n\n"
        f"⋆｡° ✮ @Universal_DownloadBot ✮ °｡⋆"
    )


# ── /mystats ─────────────────────────────────────────────────────────────────
@app.on_message(filters.command("mystats") & ~filters.outgoing)
async def cmd_mystats(client, msg: Message):
    uid  = msg.from_user.id
    user = await db.check_and_reset_daily(uid)
    if not user:
        await msg.reply("Please /start the bot first.")
        return
    plan   = user.get("plan", "free")
    badge  = {"basic": "🥉", "premium": "💎", "free": "🆓"}.get(plan, "🆓")
    limit  = ({"basic": BASIC_LIMIT, "premium": PREMIUM_LIMIT}.get(plan, FREE_LIMIT)
              if uid not in __import__("config").OWNER_IDS else 9999)
    count  = user.get("daily_count", 0)
    pct    = int(count / limit * 20) if limit else 0
    bar    = "█" * pct + "░" * (20 - pct)
    expiry = fmt_dt(user.get("plan_expiry", "")) if user.get("plan_expiry") else "Never"
    await msg.reply(
        f"»»──── 📊 My Stats ────««\n\n"
        f"▸ Plan    : {badge} {plan.capitalize()}\n"
        f"▸ Used    : {count}/{limit}\n"
        f"[{bar}]\n"
        f"▸ Expiry  : {expiry}\n"
        f"▸ Joined  : {fmt_dt(user.get('joined_at', ''))}\n\n"
        f"⋆｡° ✮ @Universal_DownloadBot ✮ °｡⋆"
    )


# ── /history ─────────────────────────────────────────────────────────────────
@app.on_message(filters.command("history") & ~filters.outgoing)
async def cmd_history(client, msg: Message):
    rows = await db.get_history(msg.from_user.id)
    if not rows:
        await msg.reply("»»──── 📋 History ────««\n\nNo downloads yet!")
        return
    lines = "\n".join(
        f"▸ {r['title'][:40]} ({fmt_size(r['file_size'] or 0)})" for r in rows
    )
    await msg.reply(f"»»──── 📋 Last Downloads ────««\n\n{lines}\n\n⋆｡° ✮ @Universal_DownloadBot ✮ °｡⋆")


# ── /queue ───────────────────────────────────────────────────────────────────
@app.on_message(filters.command("queue") & ~filters.outgoing)
async def cmd_queue(client, msg: Message):
    from queue_manager import get_queue_size
    n = get_queue_size(msg.from_user.id)
    await msg.reply(
        f"»»──── 🔄 Queue ────««\n\n"
        f"▸ Pending: {n} item(s)\n\n"
        f"Use /cancel to clear your queue.\n\n"
        f"⋆｡° ✮ @Universal_DownloadBot ✮ °｡⋆"
    )


# ── /cancel ──────────────────────────────────────────────────────────────────
@app.on_message(filters.command("cancel") & ~filters.outgoing)
async def cmd_cancel(client, msg: Message):
    from queue_manager import cancel_user_queue
    n = await cancel_user_queue(msg.from_user.id)
    await msg.reply(f"»»──── ✅ Cancelled ────««\n\n▸ Removed {n} item(s) from queue.\n\n⋆｡° ✮ @Universal_DownloadBot ✮ °｡⋆")


# ── /settings ────────────────────────────────────────────────────────────────
@app.on_message(filters.command("settings") & ~filters.outgoing)
async def cmd_settings(client, msg: Message):
    uid  = msg.from_user.id
    user = await db.get_user(uid)
    plan  = user.get("plan", "free") if user else "free"
    badge = {"basic": "🥉", "premium": "💎", "free": "🆓"}.get(plan, "🆓")
    kbd = InlineKeyboardMarkup([
        [InlineKeyboardButton("💼 Upgrade Plan", callback_data="plans"),
         InlineKeyboardButton("📋 History",      callback_data="history")],
    ])
    await msg.reply(
        f"»»──── ⚙️ Settings ────««\n\n"
        f"▸ User ID : {uid}\n"
        f"▸ Plan    : {badge} {plan.capitalize()}\n\n"
        f"⋆｡° ✮ @Universal_DownloadBot ✮ °｡⋆",
        reply_markup=kbd
    )


# ── /feedback ────────────────────────────────────────────────────────────────
@app.on_message(filters.command("feedback") & ~filters.outgoing)
async def cmd_feedback(client, msg: Message):
    parts = msg.text.split(None, 1)
    if len(parts) < 2:
        await msg.reply("Usage: /feedback <your message>")
        return
    text = parts[1]
    await db.save_feedback(msg.from_user.id, text)
    for oid in __import__("config").OWNER_IDS:
        try:
            await client.send_message(
                oid,
                f"»»──── 💬 Feedback ────««\n\n"
                f"▸ From: @{msg.from_user.username or 'N/A'} ({msg.from_user.id})\n"
                f"▸ {text}\n\n"
                f"⋆｡° ✮ @Universal_DownloadBot ✮ °｡⋆"
            )
        except Exception:
            pass
    await msg.reply("»»──── ✅ Feedback Sent ────««\n\nThank you! Your feedback has been forwarded.\n\n⋆｡° ✮ @Universal_DownloadBot ✮ °｡⋆")


# ── Callbacks ────────────────────────────────────────────────────────────────
@app.on_callback_query(filters.regex("^(home|help|plans|stats|settings|history|check_sub)$"))
async def handle_callbacks(client, cb: CallbackQuery):
    uid  = cb.from_user.id            # CRITICAL: cb.from_user not cb.message.from_user
    data = cb.data

    if data == "check_sub":
        from utils.helpers import is_subbed
        if await is_subbed(client, uid):
            await cb.message.delete()
            await _send_home(client, cb.message.chat.id, cb.from_user)
        else:
            await cb.answer("❌ You haven't joined yet!", show_alert=True)
        return

    if data == "home":
        await cb.message.delete()
        await _send_home(client, cb.message.chat.id, cb.from_user)
        return

    if data == "help":
        await cb.message.edit(
            "»»──── 📖 Help Menu ────««\n\n"
            "▸ Send any URL to download\n"
            "▸ /audio <url>   — Download as MP3\n"
            "▸ /info <url>    — Media info\n"
            "▸ /mystats       — Your stats\n"
            "▸ /history       — Last downloads\n"
            "▸ /plans         — View plans\n"
            "▸ /feedback msg  — Send feedback\n\n"
            "⋆｡° ✮ @Universal_DownloadBot ✮ °｡⋆",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🏠 Home", callback_data="home")]])
        )
        return

    if data == "plans":
        await cb.message.edit(
            f"»»──── 💼 Plans ────««\n\n"
            f"🆓 Free    — {FREE_LIMIT}/day   — Free\n"
            f"🥉 Basic   — {BASIC_LIMIT}/day  — 30 days\n"
            f"💎 Premium — {PREMIUM_LIMIT}/day — 1 year\n\n"
            f"DM @{OWNER_USERNAME} to upgrade!\n\n"
            f"⋆｡° ✮ @Universal_DownloadBot ✮ °｡⋆",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🏠 Home", callback_data="home")]])
        )
        return

    if data == "stats":
        user = await db.check_and_reset_daily(uid)
        plan  = user.get("plan", "free") if user else "free"
        badge = {"basic": "🥉", "premium": "💎", "free": "🆓"}.get(plan, "🆓")
        limit = ({"basic": BASIC_LIMIT, "premium": PREMIUM_LIMIT}.get(plan, FREE_LIMIT)
                 if uid not in __import__("config").OWNER_IDS else 9999)
        count = user.get("daily_count", 0) if user else 0
        await cb.message.edit(
            f"»»──── 📊 Stats ────««\n\n"
            f"▸ Plan  : {badge} {plan.capitalize()}\n"
            f"▸ Used  : {count}/{limit} today\n\n"
            f"⋆｡° ✮ @Universal_DownloadBot ✮ °｡⋆",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🏠 Home", callback_data="home")]])
        )
        return

    if data == "settings":
        user = await db.get_user(uid)
        plan  = user.get("plan", "free") if user else "free"
        badge = {"basic": "🥉", "premium": "💎", "free": "🆓"}.get(plan, "🆓")
        await cb.message.edit(
            f"»»──── ⚙️ Settings ────««\n\n"
            f"▸ User ID : {uid}\n"
            f"▸ Plan    : {badge} {plan.capitalize()}\n\n"
            f"⋆｡° ✮ @Universal_DownloadBot ✮ °｡⋆",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("💼 Plans",   callback_data="plans"),
                 InlineKeyboardButton("📋 History", callback_data="history")],
                [InlineKeyboardButton("🏠 Home",    callback_data="home")],
            ])
        )
        return

    if data == "history":
        rows = await db.get_history(uid)
        if not rows:
            txt = "»»──── 📋 History ────««\n\nNo downloads yet!"
        else:
            lines = "\n".join(f"▸ {r['title'][:40]}" for r in rows)
            txt   = f"»»──── 📋 History ────««\n\n{lines}\n\n⋆｡° ✮ @Universal_DownloadBot ✮ °｡⋆"
        await cb.message.edit(txt,
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🏠 Home", callback_data="home")]]))
        return

    await cb.answer()


async def _send_home(client, chat_id, from_user):
    uid  = from_user.id
    user = await db.get_user(uid)
    plan  = user.get("plan", "free") if user else "free"
    badge = {"basic": "🥉", "premium": "💎", "free": "🆓"}.get(plan, "🆓")
    text = (
        f"⋆｡° ✮ °｡⋆\n"
        f"-ˏˋ⋆ ᴡ ᴇ ʟ ᴄ ᴏ ᴍ ᴇ ⋆ˊˎ-\n\n"
        f"»»──── 𝗦𝗲𝗿𝗲𝗻𝗮 𝗗𝗼𝘄𝗻𝗹𝗼𝗮𝗱𝗲𝗿 𝗕𝗼𝘁 ────««\n\n"
        f"▸ Hello, {from_user.first_name or 'there'}!\n"
        f"▸ Plan : {badge} {plan.capitalize()}\n\n"
        f"Just send any URL to download!\n\n"
        f"⋆ ｡˚ @{SUPPORT_USERNAME} ˚｡ ⋆"
    )
    kbd = InlineKeyboardMarkup([
        [InlineKeyboardButton("📋 Help",    callback_data="help"),
         InlineKeyboardButton("💼 Plans",   callback_data="plans")],
        [InlineKeyboardButton("📊 Stats",   callback_data="stats"),
         InlineKeyboardButton("⚙️ Settings", callback_data="settings")],
        [InlineKeyboardButton("📢 Support", url=FSUB_LINK)],
    ])
    if START_PIC:
        await client.send_photo(chat_id, START_PIC, caption=text, reply_markup=kbd)
    else:
        await client.send_message(chat_id, text, reply_markup=kbd)
