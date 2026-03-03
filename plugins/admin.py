"""
╔══════════════════════════════════════════╗
║    👑  A D M I N  H A N D L E R S         ║
╚══════════════════════════════════════════╝
"""
import asyncio, logging, os
from pyrogram import filters
from pyrogram.types import Message
from client import app
from config import Config
import database as db
from utils.decorators import owner_only
from utils.helpers import plan_badge
from plugins.start import uptime_str

logger = logging.getLogger(__name__)

@app.on_message(filters.command("givepremium") & filters.private)
@owner_only
async def give_premium_cmd(client, message: Message):
    args = message.command[1:]
    if len(args) < 2:
        await message.reply(
            "»»──── ℹ️ Usage ────««\n\n"
            "/givepremium `<user_id>` `<plan>`\n\n"
            "**Plans:** `basic` (1 month) | `premium` (1 year)",
            quote=True
        )
        return
    try:
        target_id = int(args[0])
        plan      = args[1].lower().strip()
    except ValueError:
        await message.reply("Invalid user ID.", quote=True)
        return

    if plan == "basic":
        days, label = Config.BASIC_PLAN_DAYS, "🥉 Basic (1 Month)"
    elif plan == "premium":
        days, label = Config.PREMIUM_PLAN_DAYS, "💎 Premium (1 Year)"
    else:
        await message.reply("Use `basic` or `premium`.", quote=True)
        return

    user = await db.get_user(target_id)
    if not user:
        await message.reply("User `" + str(target_id) + "` not found in database.", quote=True)
        return

    await db.set_plan(target_id, plan, days)
    try:
        await client.send_message(target_id,
            "»»──── 🎉 Plan Activated ────««\n\n"
            "🎊 Your plan upgraded to **" + label + "**!\n"
            "Thank you for supporting us! 💖\n\n"
            "»»──────────────────────────««"
        )
    except Exception:
        pass
    await message.reply(
        "»»──── ✅ Plan Granted ────««\n\n"
        "👤 User : `" + str(target_id) + "`\n"
        "🏷️  Plan : **" + label + "**\n"
        "📅 Days : **" + str(days) + "**",
        quote=True
    )

@app.on_message(filters.command("removepremium") & filters.private)
@owner_only
async def remove_premium_cmd(client, message: Message):
    args = message.command[1:]
    if not args:
        await message.reply("/removepremium `<user_id>`", quote=True)
        return
    try:
        target_id = int(args[0])
    except ValueError:
        await message.reply("Invalid ID.", quote=True)
        return
    if not await db.get_user(target_id):
        await message.reply("User `" + str(target_id) + "` not found.", quote=True)
        return
    await db.remove_plan(target_id)
    try:
        await client.send_message(target_id,
            "»»──── ℹ️ Plan Update ────««\n\n"
            "Your plan has been reverted to **Free**.\n"
            "Contact " + Config.OWNER_USERNAME + " for queries."
        )
    except Exception:
        pass
    await message.reply("Plan removed for `" + str(target_id) + "`.", quote=True)

@app.on_message(filters.command("ban") & filters.private)
@owner_only
async def ban_cmd(client, message: Message):
    args = message.command[1:]
    if not args:
        await message.reply("/ban `<user_id>`", quote=True)
        return
    try:
        uid = int(args[0])
    except ValueError:
        await message.reply("Invalid ID.", quote=True)
        return
    await db.ban_user(uid)
    try:
        await client.send_message(uid,
            "»»──── 🚫 Account Banned ────««\n\n"
            "You have been banned from using this bot.\n"
            "Contact " + Config.OWNER_USERNAME + " for appeal."
        )
    except Exception:
        pass
    await message.reply("User `" + str(uid) + "` **banned**.", quote=True)

@app.on_message(filters.command("unban") & filters.private)
@owner_only
async def unban_cmd(client, message: Message):
    args = message.command[1:]
    if not args:
        await message.reply("/unban `<user_id>`", quote=True)
        return
    try:
        uid = int(args[0])
    except ValueError:
        await message.reply("Invalid ID.", quote=True)
        return
    await db.unban_user(uid)
    try:
        await client.send_message(uid,
            "»»──── ✅ Account Unbanned ────««\n\n"
            "Your ban has been lifted. You can use the bot again!"
        )
    except Exception:
        pass
    await message.reply("User `" + str(uid) + "` **unbanned**.", quote=True)

@app.on_message(filters.command("stats") & filters.private)
@owner_only
async def stats_cmd(client, message: Message):
    total_users = await db.get_total_users()
    total_dls   = await db.get_total_downloads()
    premium     = await db.get_premium_users()
    banned      = await db.get_banned_users()
    me          = await client.get_me()
    prem_count  = len([u for u in premium if u["plan"] == "premium"])
    basic_count = len([u for u in premium if u["plan"] == "basic"])
    await message.reply(
        "»»────── 📊 BOT STATISTICS ──────««\n\n"
        "🤖 Bot         : @" + me.username + "\n"
        "⏰ Uptime      : **" + uptime_str() + "**\n"
        "👥 Total Users : **" + str(total_users) + "**\n"
        "📥 Total DLs   : **" + str(total_dls) + "**\n"
        "💎 Premium     : **" + str(prem_count) + "**\n"
        "🥉 Basic       : **" + str(basic_count) + "**\n"
        "🚫 Banned      : **" + str(len(banned)) + "**\n\n"
        "»»──────────────────────────────««",
        quote=True
    )

@app.on_message(filters.command("users") & filters.private)
@owner_only
async def users_cmd(client, message: Message):
    premium = await db.get_premium_users()
    if not premium:
        await message.reply("No premium users.", quote=True)
        return
    lines = ["»»──── 💎 PREMIUM USERS ────««\n"]
    for u in premium[:20]:
        expiry = (u.get("plan_expiry") or "")[:10]
        lines.append(
            "  [" + plan_badge(u["plan"]) + "] `" + str(u["user_id"]) + "` "
            "(@" + str(u.get("username", "?")) + ") → " + expiry
        )
    if len(premium) > 20:
        lines.append("\n  ...and " + str(len(premium) - 20) + " more")
    lines.append("\n»»──────────────────────────««")
    await message.reply("\n".join(lines), quote=True)

@app.on_message(filters.command("banned") & filters.private)
@owner_only
async def banned_cmd(client, message: Message):
    banned = await db.get_banned_users()
    if not banned:
        await message.reply("No banned users.", quote=True)
        return
    lines = ["»»──── 🚫 BANNED USERS ────««\n"]
    for u in banned[:20]:
        lines.append("  `" + str(u["user_id"]) + "` (@" + str(u.get("username", "?")) + ")")
    lines.append("\n»»──────────────────────────««")
    await message.reply("\n".join(lines), quote=True)

@app.on_message(filters.command("broadcast") & filters.private)
@owner_only
async def broadcast_cmd(client, message: Message):
    if len(message.command) < 2 and not message.reply_to_message:
        await message.reply("Usage: `/broadcast <message>` or reply to a message with /broadcast", quote=True)
        return
    user_ids = await db.get_all_user_ids()
    status   = await message.reply(
        "📡 Broadcasting to **" + str(len(user_ids)) + "** users…", quote=True)
    success = fail = 0
    for uid in user_ids:
        try:
            if message.reply_to_message:
                await message.reply_to_message.copy(uid)
            else:
                await client.send_message(uid, message.text.split(None, 1)[1])
            success += 1
        except Exception:
            fail += 1
        await asyncio.sleep(0.05)
    await client.edit_message_text(message.chat.id, status.id,
        "»»──── 📡 Broadcast Done ────««\n\n"
        "✅ Sent   : **" + str(success) + "**\n"
        "❌ Failed : **" + str(fail) + "**"
    )

@app.on_message(filters.command("restart") & filters.private)
@owner_only
async def restart_cmd(client, message: Message):
    await message.reply("»»──── 🔄 Restarting… ────««\n\nBot will restart in a moment.", quote=True)
    os.execv(__import__("sys").executable, ["python"] + __import__("sys").argv)
