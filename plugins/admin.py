import os, sys, asyncio
from datetime import datetime, timedelta
from pyrogram import Client, filters
from pyrogram.types import Message
from client import app
from utils.decorators import owner_only
import database as db
from utils.helpers import fmt_dt

PLANS_INFO = {
    "basic":   30,
    "premium": 365,
}


@app.on_message(filters.command("givepremium") & ~filters.outgoing)
@owner_only
async def cmd_givepremium(client: Client, msg: Message):
    parts = msg.text.split()
    if len(parts) < 3:
        await msg.reply("Usage: /givepremium <user_id> <basic|premium>")
        return
    uid  = int(parts[1])
    plan = parts[2].lower()
    if plan not in PLANS_INFO:
        await msg.reply("Plan must be: basic or premium")
        return
    days   = PLANS_INFO[plan]
    expiry = (datetime.utcnow() + timedelta(days=days)).isoformat()
    user   = await db.get_user(uid)
    if not user:
        await db.upsert_user(uid)
    await db.set_plan(uid, plan, expiry)
    badge = "🥉" if plan == "basic" else "💎"
    await msg.reply(
        f"»»──── ✅ Plan Activated ────««\n\n"
        f"▸ User  : {uid}\n"
        f"▸ Plan  : {badge} {plan.capitalize()}\n"
        f"▸ Expiry: {fmt_dt(expiry)}\n\n"
        f"⋆｡° ✮ @Universal_DownloadBot ✮ °｡⋆"
    )
    try:
        await client.send_message(
            uid,
            f"»»──── 🎉 Plan Upgraded ────««\n\n"
            f"▸ Your plan: {badge} {plan.capitalize()}\n"
            f"▸ Expires : {fmt_dt(expiry)}\n\n"
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
    await msg.reply(f"»»──── ✅ Plan Removed ────««\n\n▸ {uid} reverted to 🆓 Free.\n\n⋆｡° ✮ @Universal_DownloadBot ✮ °｡⋆")
    try:
        await client.send_message(uid, "»»──── ⚠️ Plan Update ────««\n\nYour plan has been reverted to 🆓 Free.\nContact @" + __import__("config").OWNER_USERNAME + " for info.\n\n⋆｡° ✮ @Universal_DownloadBot ✮ °｡⋆")
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
    await msg.reply(f"»»──── 🚫 Banned ────««\n\n▸ User {uid} has been banned.\n\n⋆｡° ✮ @Universal_DownloadBot ✮ °｡⋆")
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
    await msg.reply(f"»»──── ✅ Unbanned ────««\n\n▸ User {uid} has been unbanned.\n\n⋆｡° ✮ @Universal_DownloadBot ✮ °｡⋆")
    try:
        await client.send_message(uid, "You have been unbanned from 𝗦𝗲𝗿𝗲𝗻𝗮 𝗗𝗼𝘄𝗻𝗹𝗼𝗮𝗱𝗲𝗿 𝗕𝗼𝘁. Welcome back!")
    except Exception:
        pass


@app.on_message(filters.command("stats") & ~filters.outgoing)
@owner_only
async def cmd_admin_stats(client: Client, msg: Message):
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
async def cmd_users(client: Client, msg: Message):
    rows = await db.get_premium_users()
    if not rows:
        await msg.reply("No premium users.")
        return
    lines = "\n".join(
        f"▸ {r['user_id']} | @{r['username'] or 'N/A'} | {r['plan']} | exp: {fmt_dt(r.get('plan_expiry',''))}"
        for r in rows
    )
    await msg.reply(f"»»──── 👑 Premium Users ────««\n\n{lines}\n\n⋆｡° ✮ @Universal_DownloadBot ✮ °｡⋆")


@app.on_message(filters.command("banned") & ~filters.outgoing)
@owner_only
async def cmd_banned(client: Client, msg: Message):
    rows = await db.get_banned_users()
    if not rows:
        await msg.reply("No banned users.")
        return
    lines = "\n".join(f"▸ {r['user_id']} | @{r['username'] or 'N/A'}" for r in rows)
    await msg.reply(f"»»──── 🚫 Banned Users ────««\n\n{lines}\n\n⋆｡° ✮ @Universal_DownloadBot ✮ °｡⋆")


@app.on_message(filters.command("broadcast") & ~filters.outgoing)
@owner_only
async def cmd_broadcast(client: Client, msg: Message):
    if msg.reply_to_message:
        bcast_msg = msg.reply_to_message
        send_fn   = lambda uid: bcast_msg.copy(uid)
    else:
        parts = msg.text.split(None, 1)
        if len(parts) < 2:
            await msg.reply("Usage: /broadcast <message>  or reply to a message")
            return
        text    = parts[1]
        send_fn = lambda uid: client.send_message(uid, text)

    uids   = await db.get_all_users()
    done   = fail = 0
    status = await msg.reply(f"Broadcasting to {len(uids)} users…")
    for uid in uids:
        try:
            await send_fn(uid)
            done += 1
        except Exception:
            fail += 1
        await asyncio.sleep(0.05)
    await status.edit(
        f"»»──── 📢 Broadcast Done ────««\n\n"
        f"▸ Sent   : {done}\n"
        f"▸ Failed : {fail}\n\n"
        f"⋆｡° ✮ @Universal_DownloadBot ✮ °｡⋆"
    )


@app.on_message(filters.command("restart") & ~filters.outgoing)
@owner_only
async def cmd_restart(client: Client, msg: Message):
    await msg.reply("»»──── 🔄 Restarting… ────««\n\n⋆｡° ✮ @Universal_DownloadBot ✮ °｡⋆")
    os.execv(sys.executable, [sys.executable] + sys.argv)
