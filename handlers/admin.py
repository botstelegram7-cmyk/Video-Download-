"""
╔══════════════════════════════════════════╗
║    👑  A D M I N  H A N D L E R S          ║
╚══════════════════════════════════════════╝
"""
import asyncio, logging
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from config import Config
import database as db
from utils.decorators import owner_only
from utils.helpers import plan_badge, is_owner
from handlers.start import uptime_str

logger = logging.getLogger(__name__)

# ──────────── /givepremium ────────────
@Client.on_message(filters.command("givepremium") & filters.private)
@owner_only
async def give_premium_cmd(client: Client, message: Message):
    """
    Usage: /givepremium <user_id> <plan>
    Plans: basic | premium
    """
    args = message.command[1:]  # skip command
    if len(args) < 2:
        await message.reply(
            "»»──── ℹ️ Usage ────««\n\n"
            "/givepremium `<user_id>` `<plan>`\n\n"
            "**Plans:** `basic` (1 month) | `premium` (1 year)\n\n"
            "**Example:**\n"
            "`/givepremium 1234567890 premium`",
            quote=True
        )
        return
    try:
        target_id = int(args[0])
        plan      = args[1].lower().strip()
    except ValueError:
        await message.reply("❌ Invalid user ID.", quote=True); return

    if plan == "basic":
        days  = Config.BASIC_PLAN_DAYS
        label = "🥉 Basic (1 Month)"
    elif plan == "premium":
        days  = Config.PREMIUM_PLAN_DAYS
        label = "💎 Premium (1 Year)"
    else:
        await message.reply("❌ Invalid plan. Use `basic` or `premium`.", quote=True); return

    user = await db.get_user(target_id)
    if not user:
        await message.reply(f"❌ User `{target_id}` not found in database.", quote=True); return

    await db.set_plan(target_id, plan, days)

    # Notify user
    try:
        await client.send_message(
            target_id,
            f"»»──── 🎉 Plan Activated ────««\n\n"
            f"🎊 Congratulations!\n"
            f"Your plan has been upgraded to **{label}**!\n\n"
            f"Thank you for supporting {Config.BOT_NAME} 💖\n\n"
            f"»»──────────────────────────««"
        )
    except Exception:
        pass

    await message.reply(
        f"»»──── ✅ Plan Granted ────««\n\n"
        f"👤 User    : `{target_id}`\n"
        f"🏷️  Plan    : **{label}**\n"
        f"📅 Duration: **{days} days**\n\n"
        f"User has been notified.\n"
        f"»»──────────────────────────««",
        quote=True
    )

# ──────────── /removepremium ────────────
@Client.on_message(filters.command("removepremium") & filters.private)
@owner_only
async def remove_premium_cmd(client: Client, message: Message):
    args = message.command[1:]
    if not args:
        await message.reply("/removepremium `<user_id>`", quote=True); return
    try:
        target_id = int(args[0])
    except ValueError:
        await message.reply("❌ Invalid user ID.", quote=True); return

    user = await db.get_user(target_id)
    if not user:
        await message.reply(f"❌ User `{target_id}` not found.", quote=True); return

    await db.remove_plan(target_id)
    try:
        await client.send_message(
            target_id,
            f"»»──── ℹ️ Plan Update ────««\n\n"
            f"Your plan has been **reverted to Free**.\n"
            f"Contact {Config.OWNER_USERNAME} for queries.\n"
            f"»»──────────────────────────««"
        )
    except Exception:
        pass
    await message.reply(f"✅ Plan removed for `{target_id}`.", quote=True)

# ──────────── /ban & /unban ────────────
@Client.on_message(filters.command("ban") & filters.private)
@owner_only
async def ban_cmd(client: Client, message: Message):
    args = message.command[1:]
    if not args:
        await message.reply("/ban `<user_id>`", quote=True); return
    try:
        uid = int(args[0])
    except ValueError:
        await message.reply("❌ Invalid ID", quote=True); return
    await db.ban_user(uid)
    await message.reply(f"✅ User `{uid}` has been **banned**.", quote=True)

@Client.on_message(filters.command("unban") & filters.private)
@owner_only
async def unban_cmd(client: Client, message: Message):
    args = message.command[1:]
    if not args:
        await message.reply("/unban `<user_id>`", quote=True); return
    try:
        uid = int(args[0])
    except ValueError:
        await message.reply("❌ Invalid ID", quote=True); return
    await db.unban_user(uid)
    await message.reply(f"✅ User `{uid}` has been **unbanned**.", quote=True)

# ──────────── /stats ────────────
@Client.on_message(filters.command("stats") & filters.private)
@owner_only
async def stats_cmd(client: Client, message: Message):
    total_users = await db.get_total_users()
    total_dls   = await db.get_total_downloads()
    premium     = await db.get_premium_users()
    me          = await client.get_me()
    text = (
        f"»»────── 📊 BOT STATISTICS ──────««\n\n"
        f"🤖 Bot        : @{me.username}\n"
        f"⏰ Uptime     : **{uptime_str()}**\n"
        f"👥 Total Users: **{total_users}**\n"
        f"📥 Total DLs  : **{total_dls}**\n"
        f"💎 Premium    : **{len([u for u in premium if u['plan']=='premium'])}**\n"
        f"🥉 Basic      : **{len([u for u in premium if u['plan']=='basic'])}**\n\n"
        f"»»──────────────────────────────««"
    )
    await message.reply(text, quote=True)

# ──────────── /users ────────────
@Client.on_message(filters.command("users") & filters.private)
@owner_only
async def users_cmd(client: Client, message: Message):
    premium = await db.get_premium_users()
    if not premium:
        await message.reply("No premium users found.", quote=True); return
    lines = ["»»──── 💎 PREMIUM USERS ────««\n"]
    for u in premium[:20]:  # max 20
        expiry = (u.get("plan_expiry") or "")[:10]
        lines.append(
            f"  [{plan_badge(u['plan'])}] "
            f"`{u['user_id']}` (@{u.get('username','?')}) → {expiry}"
        )
    if len(premium) > 20:
        lines.append(f"\n  ...and {len(premium)-20} more")
    lines.append("\n»»──────────────────────────««")
    await message.reply("\n".join(lines), quote=True)

# ──────────── /broadcast ────────────
@Client.on_message(filters.command("broadcast") & filters.private)
@owner_only
async def broadcast_cmd(client: Client, message: Message):
    if len(message.command) < 2 and not message.reply_to_message:
        await message.reply(
            "Usage: `/broadcast <message>` or reply to a message with `/broadcast`",
            quote=True
        )
        return
    if message.reply_to_message:
        broadcast_msg = message.reply_to_message
    else:
        text = message.text.split(None, 1)[1]

    user_ids = await db.get_all_user_ids()
    status   = await message.reply(f"📡 Broadcasting to **{len(user_ids)}** users…", quote=True)

    success = fail = 0
    for uid in user_ids:
        try:
            if message.reply_to_message:
                await broadcast_msg.copy(uid)
            else:
                await client.send_message(uid, text)
            success += 1
        except Exception:
            fail += 1
        await asyncio.sleep(0.05)  # rate limit friendly

    await client.edit_message_text(
        message.chat.id, status.id,
        f"»»──── 📡 Broadcast Done ────««\n\n"
        f"✅ Sent    : **{success}**\n"
        f"❌ Failed  : **{fail}**\n"
        f"📊 Total   : **{len(user_ids)}**\n\n"
        f"»»──────────────────────────««"
    )

# ──────────── /addplan (alias) ────────────
@Client.on_message(filters.command("settings") & filters.private)
async def settings_cmd(client: Client, message: Message):
    uid  = message.from_user.id
    user = await db.get_user(uid)
    plan = user.get("plan", "free") if user else "free"
    await message.reply(
        f"»»──── ⚙️ SETTINGS ────««\n\n"
        f"🏷️  Plan     : **{plan_badge(plan)}**\n\n"
        f"More settings coming soon!\n"
        f"»»──────────────────────««",
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton("💎 Upgrade", callback_data="plans_info")
        ]]),
        quote=True
    )
