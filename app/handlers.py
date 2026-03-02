"""
╔══════════════════════════════════════════════════════╗
║  📦  A L L  H A N D L E R S  ( S I N G L E  F I L E ) ║
║  start • download • admin — all in one place        ║
╚══════════════════════════════════════════════════════╝
"""
import os, asyncio, logging, time, datetime
from pyrogram import filters
from pyrogram.types import (
    Message, CallbackQuery,
    InlineKeyboardMarkup, InlineKeyboardButton
)
from client import app
from config import Config
import database as db
from utils.helpers import (
    is_owner, is_subscribed, plan_badge, format_datetime,
    extract_urls_from_text, detect_url_type,
    temp_dir_for_user, cleanup
)
from utils.progress import build_progress_text, build_queue_text, build_done_text
from utils.decorators import check_ban, force_subscribe, check_limit, owner_only
from downloader.universal import download_url
from downloader.processor import (
    extract_video_thumbnail, extract_pdf_thumbnail,
    prepare_thumbnail, build_caption, inject_video_metadata,
    make_telegram_streamable, get_video_info
)
from queue_manager import queue_manager

logger = logging.getLogger(__name__)
BOT_START_TIME = datetime.datetime.now()

VIDEO_EXTS = {"mp4","mkv","avi","mov","webm","flv","ts","wmv","m4v"}
AUDIO_EXTS = {"mp3","aac","flac","wav","ogg","m4a","opus"}
IMAGE_EXTS = {"jpg","jpeg","png","gif","webp","bmp"}

# ══════════════════════════════════════════════════════
#  UTILITIES
# ══════════════════════════════════════════════════════
def uptime_str():
    d = datetime.datetime.now() - BOT_START_TIME
    return f"{d.days}d {d.seconds//3600}h {(d.seconds%3600)//60}m"

async def show_plans(target):
    text = (
        f"»»────── 💎 PLANS & PRICING ──────««\n\n"
        f"🆓 **Free Plan**\n"
        f"   ▸ {Config.BASIC_DAILY_LIMIT} downloads / day\n\n"
        f"🥉 **Basic Plan** — _1 Month_\n"
        f"   ▸ {Config.BASIC_DAILY_LIMIT} downloads / day\n"
        f"   ▸ All sites + Terabox • Priority queue\n\n"
        f"💎 **Premium Plan** — _1 Year_\n"
        f"   ▸ {Config.PREMIUM_DAILY_LIMIT} downloads / day\n"
        f"   ▸ All features + VIP support\n\n"
        f"»»────── 💳 HOW TO BUY ──────««\n"
        f"  1️⃣  Contact owner / support\n"
        f"  2️⃣  Pay via UPI / QR\n"
        f"  3️⃣  Send screenshot → Plan activated!\n\n"
        f"»»──────────────────────────────««"
    )
    btn = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("👑 Owner",   url=f"https://t.me/{Config.OWNER_USERNAME.strip('@')}"),
            InlineKeyboardButton("📞 Support", url=f"https://t.me/{Config.OWNER_USERNAME2.strip('@')}"),
        ],
        [InlineKeyboardButton("🏠 Back", callback_data="back_home")]
    ])
    await target.reply(text, reply_markup=btn, quote=True)

async def send_help(target):
    text = (
        f"»»──────── 📖 HELP MENU ────────««\n\n"
        f"Just send me any **link** and I'll download it!\n\n"
        f"»»────── 📥 Supported ──────««\n"
        f"  🎥  YouTube • Shorts • Music\n"
        f"  📸  Instagram Reels / Posts\n"
        f"  📦  Terabox (all variants)\n"
        f"  🌊  M3U8 / HLS streams\n"
        f"  🔗  Any direct download link\n"
        f"  📄  .txt file with multiple links\n"
        f"  🌐  1000+ sites via yt-dlp\n\n"
        f"»»────── ⌨️ Commands ──────««\n"
        f"  /start    /help    /cancel\n"
        f"  /mystats  /queue   /status\n"
        f"  /plans    /buy     /settings\n\n"
        f"»»────── 👑 Admin ──────««\n"
        f"  /givepremium [id] [plan]\n"
        f"  /removepremium [id]\n"
        f"  /ban [id]  /unban [id]\n"
        f"  /broadcast [msg]\n"
        f"  /stats     /users\n\n"
        f"»»──────────────────────────────««"
    )
    btn = InlineKeyboardMarkup([[
        InlineKeyboardButton("🏠 Home",  callback_data="back_home"),
        InlineKeyboardButton("💎 Plans", callback_data="plans_info"),
    ]])
    await target.reply(text, reply_markup=btn, quote=True)

# ══════════════════════════════════════════════════════
#  START / HELP / INFO HANDLERS
# ══════════════════════════════════════════════════════
@app.on_message(filters.command("start") & filters.private)
async def start_cmd(client, message: Message):
    user = message.from_user
    await db.get_or_create_user(user.id, user.username, user.first_name)

    if not is_owner(user.id) and not await is_subscribed(client, user.id):
        btn = InlineKeyboardMarkup([[
            InlineKeyboardButton("📢 Join Channel", url=Config.FORCE_SUB_CHANNEL),
            InlineKeyboardButton("✅ I Joined",     callback_data="check_sub"),
        ]])
        await message.reply(
            f"-ˏˋ⋆ ᴡ ᴇ ʟ ᴄ ᴏ ᴍ ᴇ ⋆ˊˎ-\n\n"
            f"🌸 Hello **{user.first_name}**!\n\n"
            f"⚠️ Please **join our channel** first, then click ✅ I Joined.",
            reply_markup=btn, quote=True
        )
        return

    db_user = await db.get_user(user.id)
    plan    = (db_user or {}).get("plan", "free")

    buttons = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("📖 Help",         callback_data="help_main"),
            InlineKeyboardButton("💎 Plans",         callback_data="plans_info"),
        ],
        [
            InlineKeyboardButton("📊 My Stats",     callback_data="my_stats"),
            InlineKeyboardButton("🔔 Updates",      url=Config.FORCE_SUB_CHANNEL),
        ],
        [
            InlineKeyboardButton("👑 Owner",        url=f"https://t.me/{Config.OWNER_USERNAME.strip('@')}"),
            InlineKeyboardButton("📞 Support",      url=f"https://t.me/{Config.OWNER_USERNAME2.strip('@')}"),
        ],
    ])
    caption = (
        f"⋆｡° ✮ °｡⋆\n"
        f"-ˏˋ⋆ ᴡ ᴇ ʟ ᴄ ᴏ ᴍ ᴇ ⋆ˊˎ-\n\n"
        f"✨ Hello **{user.first_name}**!\n"
        f"I am **{Config.BOT_NAME}**\n\n"
        f"»»──── 🌐 What I Can Do ────««\n"
        f"▸ YouTube • Instagram • Terabox\n"
        f"▸ M3U8 / HLS • Direct Links\n"
        f"▸ .txt Batch Downloads\n"
        f"▸ Telegram-Playable Videos\n"
        f"▸ Auto Thumbnail + Metadata\n\n"
        f"🏷️  Plan : **{plan_badge(plan)}**\n"
        f"⋆ ｡˚ ⋆  Send any link to start!  ⋆ ˚｡ ⋆"
    )
    try:
        if Config.START_PIC:
            await message.reply_photo(Config.START_PIC, caption=caption, reply_markup=buttons)
            return
    except Exception:
        pass
    await message.reply(caption, reply_markup=buttons)

@app.on_message(filters.command("help") & filters.private)
async def help_cmd(client, message: Message):
    await send_help(message)

@app.on_message(filters.command("status") & filters.private)
async def status_cmd(client, message: Message):
    me = await client.get_me()
    await message.reply(
        f"»»────── 📊 BOT STATUS ──────««\n\n"
        f"🤖 Bot    : @{me.username}\n"
        f"⏰ Uptime : **{uptime_str()}**\n"
        f"👥 Users  : **{await db.get_total_users()}**\n"
        f"📥 DLs    : **{await db.get_total_downloads()}**\n\n"
        f"»»──────────────────────────««",
        quote=True
    )

@app.on_message(filters.command(["plans","buy"]) & filters.private)
async def plans_cmd(client, message: Message):
    await show_plans(message)

@app.on_message(filters.command("mystats") & filters.private)
async def mystats_cmd(client, message: Message):
    uid  = message.from_user.id
    user = await db.check_and_reset_daily(uid)
    if not user:
        await message.reply("Use /start first.", quote=True); return
    used, limit = await db.get_user_limit(user)
    plan   = user.get("plan","free")
    expiry = (user.get("plan_expiry") or "")[:10] or "—"
    await message.reply(
        f"»»────── 👤 MY STATS ──────««\n\n"
        f"🆔 ID      : `{uid}`\n"
        f"🏷️  Plan    : **{plan_badge(plan)}**\n"
        f"📅 Expires : **{expiry}**\n"
        f"📥 Today   : **{used} / {limit}**\n"
        f"🗓️  Joined  : **{(user.get('joined_at') or '')[:10]}**\n\n"
        f"»»──────────────────────────««",
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton("💎 Upgrade", callback_data="plans_info"),
        ]]),
        quote=True
    )

@app.on_message(filters.command("settings") & filters.private)
async def settings_cmd(client, message: Message):
    user = await db.get_user(message.from_user.id)
    plan = (user or {}).get("plan","free")
    await message.reply(
        f"»»──── ⚙️ SETTINGS ────««\n\n🏷️  Plan : **{plan_badge(plan)}**\n\n"
        f"More settings coming soon!",
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton("💎 Upgrade", callback_data="plans_info")
        ]]),
        quote=True
    )

# ── Callbacks ──────────────────────────────────────
@app.on_callback_query(filters.regex("^check_sub$"))
async def check_sub_cb(client, cb: CallbackQuery):
    if await is_subscribed(client, cb.from_user.id):
        await cb.answer("✅ Verified! You can now use the bot.", show_alert=True)
        await cb.message.delete()
    else:
        await cb.answer("❌ Not joined yet! Please join first.", show_alert=True)

@app.on_callback_query(filters.regex("^back_home$"))
async def back_home_cb(client, cb: CallbackQuery):
    await cb.answer()
    await cb.message.delete()

@app.on_callback_query(filters.regex("^help_main$"))
async def help_cb(client, cb: CallbackQuery):
    await cb.answer()
    await send_help(cb.message)

@app.on_callback_query(filters.regex("^plans_info$"))
async def plans_cb(client, cb: CallbackQuery):
    await cb.answer()
    await show_plans(cb.message)

@app.on_callback_query(filters.regex("^my_stats$"))
async def my_stats_cb(client, cb: CallbackQuery):
    await cb.answer()
    await mystats_cmd(client, cb.message)

@app.on_callback_query(filters.regex("^buy_premium$"))
async def buy_premium_cb(client, cb: CallbackQuery):
    await cb.answer()
    await show_plans(cb.message)

# ══════════════════════════════════════════════════════
#  DOWNLOAD HANDLERS
# ══════════════════════════════════════════════════════
def _make_progress_cb(client, chat_id, msg_id, filename, action="dl"):
    last = [0.0]
    async def cb(current, total, speed, elapsed):
        now = time.time()
        if now - last[0] < Config.PROGRESS_UPDATE_INTERVAL:
            return
        last[0] = now
        try:
            await client.edit_message_text(
                chat_id, msg_id,
                build_progress_text(action, current, total, speed, elapsed, filename)
            )
        except Exception:
            pass
    return cb

async def _smart_upload(client, chat_id, file_path, info, caption, thumb):
    ext = (info.get("ext") or os.path.splitext(file_path)[1].lstrip(".")).lower()
    btn = InlineKeyboardMarkup([[
        InlineKeyboardButton("👑 Owner",   url=f"https://t.me/{Config.OWNER_USERNAME.strip('@')}"),
        InlineKeyboardButton("📞 Support", url=f"https://t.me/{Config.OWNER_USERNAME2.strip('@')}"),
    ]])
    if ext in VIDEO_EXTS:
        vi = await get_video_info(file_path)
        await client.send_video(
            chat_id, video=file_path, caption=caption, thumb=thumb,
            width=vi.get("width",0), height=vi.get("height",0),
            duration=int(vi.get("duration",0)),
            supports_streaming=True, reply_markup=btn,
        )
    elif ext in AUDIO_EXTS:
        await client.send_audio(
            chat_id, audio=file_path, caption=caption, thumb=thumb,
            title=info.get("title",""), performer=info.get("uploader",""),
            reply_markup=btn,
        )
    elif ext in IMAGE_EXTS:
        await client.send_photo(chat_id, photo=file_path, caption=caption, reply_markup=btn)
    elif ext == "pdf":
        th = thumb or await extract_pdf_thumbnail(file_path, os.path.dirname(file_path))
        await client.send_document(chat_id, document=file_path, caption=caption, thumb=th, reply_markup=btn)
    else:
        await client.send_document(chat_id, document=file_path, caption=caption, thumb=thumb, reply_markup=btn)

async def _process_url(client, url, user_id, chat_id, reply_id):
    pm = await client.send_message(
        chat_id, f"»»──── 🔍 Analyzing... ────««\n\n`{url[:60]}`",
        reply_to_message_id=reply_id
    )
    try:
        start    = time.time()
        url_type = detect_url_type(url)
        dl_cb    = _make_progress_cb(client, chat_id, pm.id, url.split("/")[-1][:30], "dl")
        info     = await download_url(url, user_id, progress_cb=dl_cb)

        if not info.get("path") or not os.path.exists(info["path"]):
            raise RuntimeError("File not found after download")

        fp    = info["path"]
        fsize = os.path.getsize(fp)
        ext   = (info.get("ext") or os.path.splitext(fp)[1].lstrip(".")).lower()
        title = info.get("title", os.path.basename(fp))

        if fsize > Config.MAX_FILE_SIZE:
            await client.edit_message_text(chat_id, pm.id,
                f"»»──── ❌ Too Large ────««\n{fsize//1024//1024} MB > limit"); cleanup(fp); return

        if ext in VIDEO_EXTS:
            await client.edit_message_text(chat_id, pm.id, "»»── 🔧 Processing video... ──««")
            fp = await make_telegram_streamable(fp)

        out_dir = os.path.dirname(fp)
        thumb   = info.get("thumbnail")
        if not thumb and ext in VIDEO_EXTS: thumb = await extract_video_thumbnail(fp, out_dir)
        if not thumb and ext == "pdf":      thumb = await extract_pdf_thumbnail(fp, out_dir)
        if thumb: thumb = await prepare_thumbnail(thumb)

        if ext in VIDEO_EXTS:
            fp = await inject_video_metadata(fp, title,
                artist=info.get("uploader",""),
                comment=f"Downloaded by {Config.BOT_NAME} | {format_datetime()}")

        user    = await db.get_user(user_id)
        me      = await client.get_me()
        caption = build_caption(
            title=title, file_size=fsize, url_type=url_type,
            user_id=user_id, username=(user or {}).get("username",""),
            bot_username=me.username, uploader=info.get("uploader",""),
            duration=info.get("duration",0), download_date=format_datetime(),
        )

        await client.edit_message_text(chat_id, pm.id,
            build_progress_text("up", 0, fsize, 0, 0, os.path.basename(fp)))
        await _smart_upload(client, chat_id, fp, info, caption, thumb)

        elapsed = time.time() - start
        await client.edit_message_text(chat_id, pm.id,
            build_done_text(os.path.basename(fp), fsize, elapsed, fsize/elapsed if elapsed else 0))

        if Config.LOG_CHANNEL:
            try: await client.forward_messages(Config.LOG_CHANNEL, chat_id, [pm.id])
            except Exception: pass

        await db.increment_daily(user_id)
        await db.log_download(user_id, url, title, fsize, "done")
        cleanup(fp)
        if thumb: cleanup(thumb)

    except asyncio.CancelledError:
        await client.edit_message_text(chat_id, pm.id, "»»──── ❌ Cancelled ────««"); raise
    except Exception as e:
        logger.error(f"DL error: {e}", exc_info=True)
        await client.edit_message_text(chat_id, pm.id,
            f"»»──── ❌ Failed ────««\n\n`{url[:60]}`\n\n**Error:** `{str(e)[:200]}`")
        await db.log_download(user_id, url, "", 0, "failed")

async def _queue_and_process(client, urls, user_id, chat_id, reply_id):
    for url in urls:
        task = await queue_manager.add_task(user_id, url, reply_id, chat_id)
        pos  = queue_manager.get_position(task.task_id)
        if pos > 1:
            qm = await client.send_message(chat_id,
                build_queue_text(pos, queue_manager.queue_size(), url.split("/")[-1][:30]),
                reply_to_message_id=reply_id)
            try: await asyncio.wait_for(task.future, timeout=Config.DOWNLOAD_TIMEOUT)
            except (asyncio.TimeoutError, asyncio.CancelledError):
                await client.edit_message_text(chat_id, qm.id, "»»──── ⏰ Timed Out ────««"); continue
            try: await qm.delete()
            except Exception: pass
        else:
            if not task.future.done(): task.future.set_result("start")
        if task.status == "cancelled": continue
        await _process_url(client, url, user_id, chat_id, reply_id)
        await asyncio.sleep(0.5)

IGNORE_CMDS = ["start","help","cancel","mystats","queue","status","plans","buy",
               "settings","givepremium","removepremium","ban","unban","broadcast","stats","users"]

@app.on_message(filters.private & filters.text & ~filters.command(IGNORE_CMDS))
@check_ban
@force_subscribe
@check_limit
async def text_link_handler(client, message: Message):
    urls = extract_urls_from_text(message.text or "")
    if not urls:
        await message.reply(
            "»»──── ℹ️ No URL ────««\n\nSend a valid link or .txt file.\n/help for info.",
            quote=True); return
    await message.reply(f"»»── 📋 {len(urls)} URL(s) queued ──««", quote=True)
    asyncio.ensure_future(_queue_and_process(client, urls, message.from_user.id, message.chat.id, message.id))

@app.on_message(filters.private & filters.document)
@check_ban
@force_subscribe
@check_limit
async def document_handler(client, message: Message):
    doc = message.document
    if doc and doc.file_name and doc.file_name.lower().endswith(".txt"):
        sm = await message.reply("»»── 📄 Reading links file… ──««", quote=True)
        out_dir  = temp_dir_for_user(message.from_user.id)
        txt_path = os.path.join(out_dir, "links.txt")
        await message.download(file_name=txt_path)
        with open(txt_path, "r", errors="ignore") as f: content = f.read()
        urls = extract_urls_from_text(content)
        if not urls:
            await client.edit_message_text(message.chat.id, sm.id,
                "»»──── ❌ No URLs found ────««"); return
        await client.edit_message_text(message.chat.id, sm.id,
            f"»»── ✅ {len(urls)} URLs found ──««\nQueuing…")
        asyncio.ensure_future(_queue_and_process(client, urls, message.from_user.id, message.chat.id, message.id))
    else:
        await message.reply("Only **.txt** files supported.", quote=True)

@app.on_message(filters.command("cancel") & filters.private)
async def cancel_cmd(client, message: Message):
    count = await queue_manager.cancel_user_tasks(message.from_user.id)
    await message.reply(f"»»──── ❌ Cancelled {count} task(s) ────««", quote=True)

@app.on_message(filters.command("queue") & filters.private)
async def queue_cmd(client, message: Message):
    active = queue_manager.get_user_active(message.from_user.id)
    if not active:
        await message.reply("No active downloads.", quote=True); return
    lines = ["»»────── 📋 QUEUE ──────««\n"]
    for i, t in enumerate(active, 1):
        lines.append(f"  {i}. [{t.status.upper()}] `{t.url[:40]}`")
    await message.reply("\n".join(lines), quote=True)

# ══════════════════════════════════════════════════════
#  ADMIN HANDLERS
# ══════════════════════════════════════════════════════
@app.on_message(filters.command("givepremium") & filters.private)
@owner_only
async def give_premium_cmd(client, message: Message):
    args = message.command[1:]
    if len(args) < 2:
        await message.reply("/givepremium `<user_id>` `<plan>`\nPlans: `basic` | `premium`", quote=True); return
    try: target_id = int(args[0]); plan = args[1].lower().strip()
    except ValueError: await message.reply("❌ Invalid user ID.", quote=True); return
    if plan == "basic":    days, label = Config.BASIC_PLAN_DAYS,   "🥉 Basic (1 Month)"
    elif plan == "premium": days, label = Config.PREMIUM_PLAN_DAYS, "💎 Premium (1 Year)"
    else: await message.reply("❌ Use `basic` or `premium`.", quote=True); return
    if not await db.get_user(target_id):
        await message.reply(f"❌ User `{target_id}` not found.", quote=True); return
    await db.set_plan(target_id, plan, days)
    try: await client.send_message(target_id, f"🎉 Your plan upgraded to **{label}**!")
    except Exception: pass
    await message.reply(f"✅ **{label}** granted to `{target_id}`.", quote=True)

@app.on_message(filters.command("removepremium") & filters.private)
@owner_only
async def remove_premium_cmd(client, message: Message):
    args = message.command[1:]
    if not args: await message.reply("/removepremium `<user_id>`", quote=True); return
    try: uid = int(args[0])
    except ValueError: await message.reply("❌ Invalid ID.", quote=True); return
    await db.remove_plan(uid)
    try: await client.send_message(uid, "ℹ️ Your plan has been reverted to **Free**.")
    except Exception: pass
    await message.reply(f"✅ Plan removed for `{uid}`.", quote=True)

@app.on_message(filters.command("ban") & filters.private)
@owner_only
async def ban_cmd(client, message: Message):
    args = message.command[1:]
    if not args: await message.reply("/ban `<user_id>`", quote=True); return
    try: uid = int(args[0])
    except ValueError: await message.reply("❌ Invalid ID.", quote=True); return
    await db.ban_user(uid)
    await message.reply(f"✅ `{uid}` banned.", quote=True)

@app.on_message(filters.command("unban") & filters.private)
@owner_only
async def unban_cmd(client, message: Message):
    args = message.command[1:]
    if not args: await message.reply("/unban `<user_id>`", quote=True); return
    try: uid = int(args[0])
    except ValueError: await message.reply("❌ Invalid ID.", quote=True); return
    await db.unban_user(uid)
    await message.reply(f"✅ `{uid}` unbanned.", quote=True)

@app.on_message(filters.command("stats") & filters.private)
@owner_only
async def stats_cmd(client, message: Message):
    premium = await db.get_premium_users()
    me      = await client.get_me()
    await message.reply(
        f"»»────── 📊 STATISTICS ──────««\n\n"
        f"🤖 Bot     : @{me.username}\n"
        f"⏰ Uptime  : **{uptime_str()}**\n"
        f"👥 Users   : **{await db.get_total_users()}**\n"
        f"📥 DLs     : **{await db.get_total_downloads()}**\n"
        f"💎 Premium : **{len([u for u in premium if u['plan']=='premium'])}**\n"
        f"🥉 Basic   : **{len([u for u in premium if u['plan']=='basic'])}**\n\n"
        f"»»──────────────────────────────««", quote=True)

@app.on_message(filters.command("users") & filters.private)
@owner_only
async def users_cmd(client, message: Message):
    premium = await db.get_premium_users()
    if not premium: await message.reply("No premium users.", quote=True); return
    lines = ["»»──── 💎 PREMIUM USERS ────««\n"]
    for u in premium[:20]:
        lines.append(f"  [{plan_badge(u['plan'])}] `{u['user_id']}` → {(u.get('plan_expiry') or '')[:10]}")
    if len(premium) > 20: lines.append(f"\n  ...and {len(premium)-20} more")
    await message.reply("\n".join(lines), quote=True)

@app.on_message(filters.command("broadcast") & filters.private)
@owner_only
async def broadcast_cmd(client, message: Message):
    if len(message.command) < 2 and not message.reply_to_message:
        await message.reply("Usage: `/broadcast <text>` or reply to a message.", quote=True); return
    user_ids = await db.get_all_user_ids()
    sm = await message.reply(f"📡 Broadcasting to **{len(user_ids)}** users…", quote=True)
    ok = fail = 0
    for uid in user_ids:
        try:
            if message.reply_to_message: await message.reply_to_message.copy(uid)
            else: await client.send_message(uid, message.text.split(None,1)[1])
            ok += 1
        except Exception: fail += 1
        await asyncio.sleep(0.05)
    await client.edit_message_text(message.chat.id, sm.id,
        f"»»──── 📡 Done ────««\n\n✅ {ok} sent  ❌ {fail} failed")
