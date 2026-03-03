"""
╔══════════════════════════════════════════╗
║  📥  D O W N L O A D  H A N D L E R      ║
╚══════════════════════════════════════════╝
"""
import os, asyncio, logging, time
from pyrogram import filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from client import app
from config import Config
import database as db
from utils.helpers import (
    extract_urls_from_text, detect_url_type,
    temp_dir_for_user, cleanup, is_owner,
    format_datetime, human_size
)
from utils.progress import build_progress_text, build_queue_text, build_done_text
from utils.decorators import check_ban, force_subscribe, check_limit
from downloader.universal import download_url, ytdlp_info_only
from downloader.processor import (
    extract_video_thumbnail, extract_pdf_thumbnail,
    prepare_thumbnail, build_caption, inject_video_metadata,
    make_telegram_streamable, get_video_info
)
from queue_manager import queue_manager

logger = logging.getLogger(__name__)

VIDEO_EXTS = {"mp4", "mkv", "avi", "mov", "webm", "flv", "ts", "wmv", "m4v"}
AUDIO_EXTS = {"mp3", "aac", "flac", "wav", "ogg", "m4a", "opus"}
IMAGE_EXTS = {"jpg", "jpeg", "png", "gif", "webp", "bmp"}

ALL_CMDS = [
    "start", "help", "cancel", "mystats", "queue", "status",
    "plans", "buy", "settings", "feedback", "ping", "audio",
    "info", "history",
    "givepremium", "removepremium", "ban", "unban",
    "broadcast", "stats", "users", "banned", "restart"
]

def make_progress_cb(client, chat_id, msg_id, filename, action="dl"):
    last_edit = [0.0]
    async def cb(current, total, speed, elapsed):
        now = time.time()
        if now - last_edit[0] < Config.PROGRESS_UPDATE_INTERVAL:
            return
        last_edit[0] = now
        text = build_progress_text(action, current, total, speed, elapsed, filename)
        try:
            await client.edit_message_text(chat_id, msg_id, text)
        except Exception:
            pass
    return cb

async def smart_upload(client, chat_id, file_path, info, caption, thumb):
    ext = (info.get("ext") or os.path.splitext(file_path)[1].lstrip(".")).lower()
    buttons = InlineKeyboardMarkup([[
        InlineKeyboardButton("👑 Owner",   url="https://t.me/" + Config.OWNER_USERNAME.strip("@")),
        InlineKeyboardButton("📞 Support", url="https://t.me/" + Config.OWNER_USERNAME2.strip("@")),
        InlineKeyboardButton("🔔 Channel", url=Config.FORCE_SUB_CHANNEL),
    ]])
    if ext in VIDEO_EXTS:
        vinfo = await get_video_info(file_path)
        await client.send_video(
            chat_id, video=file_path, caption=caption, thumb=thumb,
            width=vinfo.get("width", 0), height=vinfo.get("height", 0),
            duration=int(vinfo.get("duration", 0)),
            supports_streaming=True, reply_markup=buttons,
        )
    elif ext in AUDIO_EXTS:
        await client.send_audio(
            chat_id, audio=file_path, caption=caption, thumb=thumb,
            title=info.get("title", ""), performer=info.get("uploader", ""),
            reply_markup=buttons,
        )
    elif ext in IMAGE_EXTS:
        await client.send_photo(chat_id, photo=file_path, caption=caption, reply_markup=buttons)
    elif ext == "pdf":
        th = thumb or await extract_pdf_thumbnail(file_path, os.path.dirname(file_path))
        await client.send_document(chat_id, document=file_path, caption=caption, thumb=th, reply_markup=buttons)
    else:
        await client.send_document(chat_id, document=file_path, caption=caption, thumb=thumb, reply_markup=buttons)

async def process_single_url(client, url, user_id, chat_id, reply_id, audio_only=False):
    progress_msg = await client.send_message(
        chat_id,
        "»»──── 🔍 Analyzing Link… ────««\n\n`" + url[:80] + "`",
        reply_to_message_id=reply_id
    )
    prog_id = progress_msg.id
    try:
        url_type = detect_url_type(url)
        start    = time.time()
        dl_cb    = make_progress_cb(client, chat_id, prog_id, url.split("/")[-1][:30])
        info     = await download_url(url, user_id, progress_cb=dl_cb, audio_only=audio_only)

        if not info.get("path") or not os.path.exists(info["path"]):
            raise RuntimeError("Download failed — file not found after download")

        file_path = info["path"]
        file_size = os.path.getsize(file_path)
        ext       = (info.get("ext") or os.path.splitext(file_path)[1].lstrip(".")).lower()
        title     = info.get("title", os.path.basename(file_path))

        if file_size > Config.MAX_FILE_SIZE:
            await client.edit_message_text(chat_id, prog_id,
                "»»──── ❌ File Too Large ────««\n\n"
                "Size : **" + human_size(file_size) + "**\n"
                "Max  : **" + human_size(Config.MAX_FILE_SIZE) + "**"
            )
            cleanup(file_path)
            return

        if ext in VIDEO_EXTS:
            await client.edit_message_text(chat_id, prog_id,
                "»»── 🔧 Processing video… ──««\n_(Making Telegram-playable…)_")
            file_path = await make_telegram_streamable(file_path)

        out_dir = os.path.dirname(file_path)
        thumb   = info.get("thumbnail")
        if not thumb and ext in VIDEO_EXTS:
            thumb = await extract_video_thumbnail(file_path, out_dir)
        elif not thumb and ext == "pdf":
            thumb = await extract_pdf_thumbnail(file_path, out_dir)
        if thumb:
            thumb = await prepare_thumbnail(thumb)

        if ext in VIDEO_EXTS:
            file_path = await inject_video_metadata(
                file_path, title,
                artist  = info.get("uploader", ""),
                comment = "Downloaded by " + Config.BOT_NAME
            )

        user  = await db.get_user(user_id)
        uname = user.get("username") if user else ""
        me    = await client.get_me()
        caption = build_caption(
            title=title, file_size=file_size, url_type=url_type,
            user_id=user_id, username=uname, bot_username=me.username,
            uploader=info.get("uploader", ""), duration=info.get("duration", 0),
            download_date=format_datetime(),
        )

        await client.edit_message_text(chat_id, prog_id,
            build_progress_text("up", 0, file_size, 0, 0, os.path.basename(file_path)))

        await smart_upload(client, chat_id, file_path, info, caption, thumb)

        elapsed = time.time() - start
        avg_spd = file_size / elapsed if elapsed > 0 else 0
        await client.edit_message_text(chat_id, prog_id,
            build_done_text(os.path.basename(file_path), file_size, elapsed, avg_spd))

        if Config.LOG_CHANNEL:
            try:
                await client.forward_messages(Config.LOG_CHANNEL, chat_id, [prog_id])
            except Exception:
                pass

        await db.increment_daily(user_id)
        await db.log_download(user_id, url, title, file_size, "done")
        cleanup(file_path)
        if thumb: cleanup(thumb)

    except asyncio.CancelledError:
        try:
            await client.edit_message_text(chat_id, prog_id, "»»──── ❌ Download Cancelled ────««")
        except Exception:
            pass
        raise
    except Exception as e:
        logger.error("Download error [%s]: %s", url, e, exc_info=True)
        try:
            await client.edit_message_text(chat_id, prog_id,
                "»»──── ❌ Download Failed ────««\n\n`" + url[:60] + "`\n\n"
                "**Error:** `" + str(e)[:300] + "`\n\n"
                "Try again or contact " + Config.OWNER_USERNAME
            )
        except Exception:
            pass
        await db.log_download(user_id, url, "", 0, "failed")

async def queue_and_process(client, urls, user_id, chat_id, reply_id, audio_only=False):
    for url in urls:
        task = await queue_manager.add_task(user_id, url, reply_id, chat_id)
        pos  = queue_manager.get_position(task.task_id)
        if pos > 1:
            q_msg = await client.send_message(
                chat_id,
                build_queue_text(pos, queue_manager.queue_size(), url.split("/")[-1][:30]),
                reply_to_message_id=reply_id
            )
            try:
                await asyncio.wait_for(task.future, timeout=Config.DOWNLOAD_TIMEOUT)
            except (asyncio.TimeoutError, asyncio.CancelledError):
                try:
                    await client.edit_message_text(chat_id, q_msg.id, "»»──── ⏰ Task Timed Out ────««")
                except Exception:
                    pass
                continue
            try: await q_msg.delete()
            except Exception: pass
        else:
            if not task.future.done(): task.future.set_result("start")

        if task.status == "cancelled":
            continue
        await process_single_url(client, url, user_id, chat_id, reply_id, audio_only=audio_only)
        await asyncio.sleep(0.5)

# ══════════════════════════════════════════════════
#  /audio  — audio-only download
# ══════════════════════════════════════════════════
@app.on_message(filters.command("audio") & filters.private)
@check_ban
@force_subscribe
@check_limit
async def audio_cmd(client, message: Message):
    args = message.text.split(None, 1)
    if len(args) < 2:
        await message.reply(
            "»»──── 🎵 AUDIO DOWNLOAD ────««\n\n"
            "Usage: `/audio <URL>`\n\n"
            "Example:\n`/audio https://youtube.com/watch?v=xxx`\n\n"
            "Downloads **audio only** (MP3)\n\n"
            "»»──────────────────────────««",
            quote=True
        )
        return
    urls = extract_urls_from_text(args[1])
    if not urls:
        await message.reply("No valid URL found. Usage: `/audio <url>`", quote=True)
        return
    await message.reply(
        "»»── 🎵 Audio Download Queued ──««\n\nProcessing…", quote=True)
    asyncio.ensure_future(
        queue_and_process(client, urls, message.from_user.id, message.chat.id, message.id, audio_only=True)
    )

# ══════════════════════════════════════════════════
#  /info — URL info without downloading
# ══════════════════════════════════════════════════
@app.on_message(filters.command("info") & filters.private)
@check_ban
@force_subscribe
async def info_cmd(client, message: Message):
    args = message.text.split(None, 1)
    if len(args) < 2:
        await message.reply(
            "»»──── ℹ️ URL INFO ────««\n\n"
            "Usage: `/info <URL>`\n\n"
            "Gets info **without downloading**.\n\n"
            "»»──────────────────────────««",
            quote=True
        )
        return
    urls = extract_urls_from_text(args[1])
    if not urls:
        await message.reply("No valid URL found.", quote=True)
        return

    url  = urls[0]
    wait = await message.reply("»»──── 🔍 Fetching info… ────««", quote=True)
    try:
        info = await ytdlp_info_only(url)
        title    = (info.get("title") or "Unknown")[:60]
        uploader = info.get("uploader", "Unknown")
        duration = info.get("duration", 0)
        views    = info.get("view_count", 0)
        url_type = detect_url_type(url).upper()

        def hms(s):
            if not s: return "N/A"
            m, s = divmod(int(s), 60)
            h, m = divmod(m, 60)
            return ("%02d:%02d:%02d" % (h, m, s)) if h else ("%02d:%02d" % (m, s))

        text = (
            "»»──────── ℹ️ URL INFO ────────««\n\n"
            "📄 **Title**    : " + title + "\n"
            "👤 **Uploader** : " + str(uploader) + "\n"
            "🏷️  **Source**   : " + url_type + "\n"
            "⏱️  **Duration** : " + hms(duration) + "\n"
            "👁️  **Views**    : " + "{:,}".format(views) + "\n\n"
            "»»──────────────────────────────««"
        )
        await wait.edit_text(text)
    except Exception as e:
        await wait.edit_text(
            "»»──── ❌ Info Failed ────««\n\n"
            "Could not fetch info.\nError: `" + str(e)[:200] + "`"
        )

# ══════════════════════════════════════════════════
#  Text link handler (main downloader)
# ══════════════════════════════════════════════════
@app.on_message(filters.private & filters.text & ~filters.command(ALL_CMDS))
@check_ban
@force_subscribe
@check_limit
async def text_link_handler(client, message: Message):
    urls = extract_urls_from_text(message.text or "")
    if not urls:
        await message.reply(
            "»»──── ℹ️ No URL Found ────««\n\n"
            "Send a **valid URL** or **.txt file** with links.\n"
            "Type /help for instructions.",
            quote=True
        )
        return
    await message.reply(
        "»»── 📋 " + str(len(urls)) + " URL(s) Queued ──««\n\nProcessing now…", quote=True)
    asyncio.ensure_future(
        queue_and_process(client, urls, message.from_user.id, message.chat.id, message.id)
    )

# ══════════════════════════════════════════════════
#  Document (.txt file) handler
# ══════════════════════════════════════════════════
@app.on_message(filters.private & filters.document)
@check_ban
@force_subscribe
@check_limit
async def document_handler(client, message: Message):
    doc = message.document
    if doc and doc.file_name and doc.file_name.lower().endswith(".txt"):
        status_msg = await message.reply("»»── 📄 Reading links file… ──««", quote=True)
        out_dir    = temp_dir_for_user(message.from_user.id)
        txt_path   = os.path.join(out_dir, "links.txt")
        await message.download(file_name=txt_path)
        with open(txt_path, "r", errors="ignore") as f:
            content = f.read()
        urls = extract_urls_from_text(content)
        if not urls:
            await client.edit_message_text(message.chat.id, status_msg.id,
                "»»──── ❌ No URLs Found ────««\n\nNo valid URLs found in your .txt file.")
            return
        await client.edit_message_text(message.chat.id, status_msg.id,
            "»»── ✅ Found **" + str(len(urls)) + " URLs** ──««\nQueuing all downloads…")
        asyncio.ensure_future(
            queue_and_process(client, urls, message.from_user.id, message.chat.id, message.id)
        )
    else:
        await message.reply(
            "»»──── ℹ️ Unsupported File ────««\n\n"
            "Only **.txt** files with links are supported.",
            quote=True
        )

# ══════════════════════════════════════════════════
#  /cancel  /queue
# ══════════════════════════════════════════════════
@app.on_message(filters.command("cancel") & filters.private)
async def cancel_cmd(client, message: Message):
    count = await queue_manager.cancel_user_tasks(message.from_user.id)
    await message.reply(
        "»»──── ❌ CANCELLED ────««\n\nCancelled **" + str(count) + "** pending download(s).",
        quote=True
    )

@app.on_message(filters.command("queue") & filters.private)
async def queue_cmd(client, message: Message):
    active = queue_manager.get_user_active(message.from_user.id)
    if not active:
        await message.reply("»»──── 📋 QUEUE ────««\n\nNo active downloads.", quote=True)
        return
    lines = ["»»────── 📋 YOUR QUEUE ──────««\n"]
    for i, t in enumerate(active, 1):
        lines.append("  " + str(i) + ". [" + t.status.upper() + "] `" + t.url[:40] + "`")
    lines.append("\n»»──────────────────────────««")
    await message.reply("\n".join(lines), quote=True)
