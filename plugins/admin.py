"""
╔══════════════════════════════════════════════════════════╗
║   👑  ADMIN  PANEL                                       ║
║   givepremium · ban · broadcast · stats · restart        ║
╚══════════════════════════════════════════════════════════╝
"""
import asyncio, logging, os, sys
from pyrogram import filters
from pyrogram.types import Message
from client import app
from config import Config
import database as db
from utils.decorators import owner_only
from utils.helpers import plan_badge
from plugins.start import uptime

log = logging.getLogger(__name__)

# ════════════════════════════════════════════
#  /givepremium
# ════════════════════════════════════════════
@app.on_message(filters.command("givepremium") & ~filters.outgoing)
@owner_only
async def cmd_giveprem(client, msg: Message):
    args = msg.command[1:]
    if len(args) < 2:
        await msg.reply(
            "»»──── ℹ️ USAGE ────««\n\n"
            "/givepremium `<user_id>` `<plan>`\n\n"
            "**Plans:** `basic` (1 month) | `premium` (1 year)",
            quote=True
        ); return
    try:
        uid  = int(args[0])
        plan = args[1].lower().strip()
    except ValueError:
        await msg.reply("❌ Invalid user ID.", quote=True); return

    if plan == "basic":
        days, label = Config.BASIC_DAYS,   "🥉 Basic (1 Month)"
    elif plan == "premium":
        days, label = Config.PREMIUM_DAYS, "💎 Premium (1 Year)"
    else:
        await msg.reply("❌ Plan must be `basic` or `premium`.", quote=True); return

    if not await db.get_user(uid):
        await msg.reply(f"❌ User `{uid}` not found.", quote=True); return

    await db.set_plan(uid, plan, days)
    try:
        await client.send_message(
            uid,
            "»»──── 🎉 Plan Activated! ────««\n\n"
            f"🎊 Your plan: **{label}**\n"
            "Thank you! 💖\n\n"
            "»»──────────────────────────««"
        )
    except: pass
    await msg.reply(
        "»»──── ✅ Done ────««\n\n"
        f"👤 User : `{uid}`\n"
        f"🏷️  Plan : **{label}**\n"
        f"📅 Days : **{days}**",
        quote=True
    )

# ════════════════════════════════════════════
#  /removepremium
# ════════════════════════════════════════════
@app.on_message(filters.command("removepremium") & ~filters.outgoing)
@owner_only
async def cmd_remprem(client, msg: Message):
    args = msg.command[1:]
    if not args:
        await msg.reply("/removepremium `<user_id>`", quote=True); return
    try: uid = int(args[0])
    except ValueError:
        await msg.reply("❌ Invalid ID.", quote=True); return
    if not await db.get_user(uid):
        await msg.reply(f"❌ User `{uid}` not found.", quote=True); return
    await db.remove_plan(uid)
    try:
        await client.send_message(uid,
            "»»──── ℹ️ Plan Update ────««\n\n"
            "Your plan has been reverted to **Free**.\n"
            f"Contact @{Config.OWNER_UNAME} for queries.")
    except: pass
    await msg.reply(f"✅ Plan removed for `{uid}`.", quote=True)

# ════════════════════════════════════════════
#  /ban  /unban
# ════════════════════════════════════════════
@app.on_message(filters.command("ban") & ~filters.outgoing)
@owner_only
async def cmd_ban(client, msg: Message):
    args = msg.command[1:]
    if not args:
        await msg.reply("/ban `<user_id>`", quote=True); return
    try: uid = int(args[0])
    except ValueError:
        await msg.reply("❌ Invalid ID.", quote=True); return
    await db.ban(uid)
    try:
        await client.send_message(uid,
            "»»──── 🚫 Banned ────««\n\n"
            "You have been banned.\n"
            f"Contact @{Config.OWNER_UNAME} to appeal.")
    except: pass
    await msg.reply(f"🚫 Banned `{uid}`.", quote=True)

@app.on_message(filters.command("unban") & ~filters.outgoing)
@owner_only
async def cmd_unban(client, msg: Message):
    args = msg.command[1:]
    if not args:
        await msg.reply("/unban `<user_id>`", quote=True); return
    try: uid = int(args[0])
    except ValueError:
        await msg.reply("❌ Invalid ID.", quote=True); return
    await db.unban(uid)
    try:
        await client.send_message(uid,
            "»»──── ✅ Unbanned ────««\n\nYour ban has been lifted!")
    except: pass
    await msg.reply(f"✅ Unbanned `{uid}`.", quote=True)

# ════════════════════════════════════════════
#  /stats
# ════════════════════════════════════════════
@app.on_message(filters.command("stats") & ~filters.outgoing)
@owner_only
async def cmd_stats(client, msg: Message):
    tu   = await db.total_users()
    td   = await db.total_downloads()
    prem = await db.premium_users()
    ban  = await db.banned_users()
    me   = await client.get_me()
    p    = sum(1 for u in prem if u["plan"]=="premium")
    b    = sum(1 for u in prem if u["plan"]=="basic")
    await msg.reply(
        "»»──────── 📊 BOT STATS ────────««\n\n"
        f"🤖 Bot      : @{me.username}\n"
        f"⏰ Uptime   : **{uptime()}**\n"
        f"👥 Users    : **{tu}**\n"
        f"📥 DLs Done : **{td}**\n"
        f"💎 Premium  : **{p}**\n"
        f"🥉 Basic    : **{b}**\n"
        f"🚫 Banned   : **{len(ban)}**\n\n"
        "»»──────────────────────────────««",
        quote=True
    )

# ════════════════════════════════════════════
#  /users
# ════════════════════════════════════════════
@app.on_message(filters.command("users") & ~filters.outgoing)
@owner_only
async def cmd_users(client, msg: Message):
    prem = await db.premium_users()
    if not prem:
        await msg.reply("No premium users.", quote=True); return
    lines = ["»»──── 💎 PREMIUM USERS ────««\n"]
    for u in prem[:25]:
        exp = (u.get("plan_expiry") or "")[:10]
        lines.append(
            f"  [{plan_badge(u['plan'])}] `{u['user_id']}` "
            f"(@{u.get('username','?')}) → {exp}"
        )
    if len(prem) > 25:
        lines.append(f"\n  …and {len(prem)-25} more")
    lines.append("\n»»──────────────────────────««")
    await msg.reply("\n".join(lines), quote=True)

# ════════════════════════════════════════════
#  /banned
# ════════════════════════════════════════════
@app.on_message(filters.command("banned") & ~filters.outgoing)
@owner_only
async def cmd_banned(client, msg: Message):
    ban = await db.banned_users()
    if not ban:
        await msg.reply("No banned users.", quote=True); return
    lines = ["»»──── 🚫 BANNED USERS ────««\n"]
    for u in ban[:25]:
        lines.append(f"  `{u['user_id']}` (@{u.get('username','?')})")
    lines.append("\n»»──────────────────────────««")
    await msg.reply("\n".join(lines), quote=True)

# ════════════════════════════════════════════
#  /broadcast
# ════════════════════════════════════════════
@app.on_message(filters.command("broadcast") & ~filters.outgoing)
@owner_only
async def cmd_broadcast(client, msg: Message):
    if len(msg.command) < 2 and not msg.reply_to_message:
        await msg.reply(
            "Usage: `/broadcast <message>`\nor reply to a message with /broadcast",
            quote=True
        ); return
    uids   = await db.all_user_ids()
    sm     = await msg.reply(f"📡 Sending to **{len(uids)}** users…", quote=True)
    ok = fail = 0
    for uid in uids:
        try:
            if msg.reply_to_message: await msg.reply_to_message.copy(uid)
            else: await client.send_message(uid, msg.text.split(None,1)[1])
            ok += 1
        except: fail += 1
        await asyncio.sleep(0.05)
    await sm.edit_text(
        "»»──── 📡 Broadcast Done ────««\n\n"
        f"✅ Sent   : **{ok}**\n❌ Failed : **{fail}**"
    )

# ════════════════════════════════════════════
#  /restart
# ════════════════════════════════════════════
@app.on_message(filters.command("restart") & ~filters.outgoing)
@owner_only
async def cmd_restart(client, msg: Message):
    await msg.reply("»»──── 🔄 Restarting… ────««", quote=True)
    os.execv(sys.executable, [sys.executable] + sys.argv)
