import os
import sys
import asyncio
from datetime import datetime, timedelta
from pyrogram import Client, filters
from pyrogram.types import Message
from client import app
from utils.decorators import owner_only
import database as db
from utils.helpers import fmt_dt
import config as cfg

PLANS_DAYS = {"basic": 30, "premium": 365}


@app.on_message(filters.command("givepremium") & ~filters.outgoing)
@owner_only
async def cmd_givepremium(client: Client, msg: Message):
    parts = msg.text.split()
    if len(parts) < 3:
        await msg.reply("Usage: /givepremium <user_id> <basic|premium>")
        return
    try:
        uid  = int(parts[1])
    except ValueError:
        await msg.reply("Invalid user ID.")
        return
    plan = parts[2].lower()
    if plan not in PLANS_DAYS:
        await msg.reply("Plan must be: basic or premium")
        return
    expiry = (datetime.utcnow() + timedelta(days=PLANS_DAYS[plan])).isoformat()
    user   = await db.get_user(uid)
    if not user:
        await db.upsert_user(uid)
    await db.set_plan(uid, plan, expiry)
    badge = "🥉" if plan == "basic" else "💎"
    await msg.reply(
        f"»»──── ✅ Plan Activated ────««\n\n"
        f"▸ User   : {uid}\n"
        f"▸ Plan   : {badge} {plan.capitalize()}\n"
        f"▸ Expiry : {fmt_dt(expiry)}\n\n"
        f"⋆｡° ✮ @Universal_DownloadBot ✮ °｡⋆"
    )
    try:
        await client.send_message(
            uid,
            f"»»──── 🎉 Plan Upgraded! ────««\n\n"
            f"▸ Plan   : {badge} {plan.capitalize()}\n"
            f"▸ Expiry : {fmt_dt(expiry)}\n\n"
            f"Thank you! ⋆｡° ✮ @Universal_DownloadBot ✮ °｡⋆"
        )
    except Exception:
        pass


@app.on_message(filters.command("removepremium") & ~filters.outgoing)
@owner_only
async def cmd_removepremium(client: Client, msg: Message):
    parts = msg.text.split()
    if len(parts) < 2:
        await msg.reply("Usage: /removepremium <user_id>")
        return
    uid = int(parts[1])
    await db.set_plan(uid, "free", "")
    await msg.reply(
        f"»»──── ✅ Plan Removed ────««\n\n▸ {uid} → 🆓 Free\n\n⋆｡° ✮ @Universal_DownloadBot ✮ °｡⋆"
    )
    try:
        await client.send_message(
            uid,
            f"»»──── ⚠️ Plan Update ────««\n\nYour plan → 🆓 Free.\nDM @{cfg.OWNER_USERNAME} for info."
        )
    except Exception:
        pass


@app.on_message(filters.command("ban") & ~filters.outgoing)
@owner_only
async def cmd_ban(client: Client, msg: Message):
    parts = msg.text.split()
    if len(parts) < 2:
        await msg.reply("Usage: /ban <user_id>")
        return
    uid = int(parts[1])
    await db.ban_user(uid)
    await msg.reply(
        f"»»──── 🚫 Banned ────««\n\n▸ User {uid} banned.\n\n⋆｡° ✮ @Universal_DownloadBot ✮ °｡⋆"
    )
    try:
        await client.send_message(uid, "You have been banned from 𝗦𝗲𝗿𝗲𝗻𝗮 𝗗𝗼𝘄𝗻𝗹𝗼𝗮𝗱𝗲𝗿 𝗕𝗼𝘁.")
    except Exception:
        pass


@app.on_message(filters.command("unban") & ~filters.outgoing)
@owner_only
async def cmd_unban(client: Client, msg: Message):
    parts = msg.text.split()
    if len(parts) < 2:
        await msg.reply("Usage: /unban <user_id>")
        return
    uid = int(parts[1])
    await db.unban_user(uid)
    await msg.reply(
        f"»»──── ✅ Unbanned ────««\n\n▸ User {uid} unbanned.\n\n⋆｡° ✮ @Universal_DownloadBot ✮ °｡⋆"
    )
    try:
        await client.send_message(uid, "You have been unbanned! Welcome back 🎉")
    except Exception:
        pass


@app.on_message(filters.command("stats") & ~filters.outgoing)
@owner_only
async def cmd_admin_stats(_, msg: Message):
    st = await db.get_stats()
    await msg.reply(
        f"»»──── 📊 Admin Stats ────««\n\n"
        f"▸ Total Users    : {st['total_users']}\n"
        f"▸ Total Downloads: {st['total_downloads']}\n"
        f"▸ Premium Users  : {st['premium_users']}\n"
        f"▸ Banned Users   : {st['banned_users']}\n\n"
        f"⋆｡° ✮ @Universal_DownloadBot ✮ °｡⋆"
    )


@app.on_message(filters.command("users") & ~filters.outgoing)
@owner_only
async def cmd_users(_, msg: Message):
    rows = await db.get_premium_users()
    if not rows:
        await msg.reply("No premium users.")
        return
    lines = "\n".join(
        f"▸ {r['user_id']} | @{r['username'] or 'N/A'} | "
        f"{r['plan']} | {fmt_dt(r.get('plan_expiry',''))}"
        for r in rows
    )
    await msg.reply(
        f"»»──── 👑 Premium Users ────««\n\n{lines}\n\n⋆｡° ✮ @Universal_DownloadBot ✮ °｡⋆"
    )


@app.on_message(filters.command("banned") & ~filters.outgoing)
@owner_only
async def cmd_banned(_, msg: Message):
    rows = await db.get_banned_users()
    if not rows:
        await msg.reply("No banned users.")
        return
    lines = "\n".join(f"▸ {r['user_id']} | @{r['username'] or 'N/A'}" for r in rows)
    await msg.reply(
        f"»»──── 🚫 Banned Users ────««\n\n{lines}\n\n⋆｡° ✮ @Universal_DownloadBot ✮ °｡⋆"
    )


@app.on_message(filters.command("broadcast") & ~filters.outgoing)
@owner_only
async def cmd_broadcast(client: Client, msg: Message):
    if msg.reply_to_message:
        bcast = msg.reply_to_message
        send  = lambda uid: bcast.copy(uid)
    else:
        parts = msg.text.split(None, 1)
        if len(parts) < 2:
            await msg.reply("Usage: /broadcast <text>  or reply to a message")
            return
        text = parts[1]
        send = lambda uid: client.send_message(uid, text)

    uids   = await db.get_all_users()
    done   = fail = 0
    status = await msg.reply(f"Broadcasting to {len(uids)} users…")
    for uid in uids:
        try:
            await send(uid)
            done += 1
        except Exception:
            fail += 1
        await asyncio.sleep(0.05)
    await status.edit(
        f"»»──── 📢 Broadcast Done ────««\n\n"
        f"▸ Sent   : {done}\n▸ Failed : {fail}\n\n"
        f"⋆｡° ✮ @Universal_DownloadBot ✮ °｡⋆"
    )


@app.on_message(filters.command("restart") & ~filters.outgoing)
@owner_only
async def cmd_restart(_, msg: Message):
    await msg.reply("»»──── 🔄 Restarting… ────««\n\n⋆｡° ✮ @Universal_DownloadBot ✮ °｡⋆")
    os.execv(sys.executable, [sys.executable] + sys.argv)
