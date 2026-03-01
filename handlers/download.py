"""
╔══════════════════════════════════════════╗
║  📥  D O W N L O A D  H A N D L E R       ║
╚══════════════════════════════════════════╝
Handles all link/file download requests with
queue, progress, thumbnail, metadata & upload.
"""
import os, asyncio, logging, time
from pyrogram import Client, filters
from pyrogram.types import (
    Message, InlineKeyboardMarkup, InlineKeyboardButton,
    InputMediaVideo, InputMediaDocument
)
from config import Config
import database as db
from utils.helpers import (
    extract_urls_from_text, detect_url_type,
    temp_dir_for_user, cleanup, is_owner, format_datetime
)
from utils.progress import build_progress_text, build_queue_text, build_done_text
from utils.decorators import check_ban, force_subscribe, check_limit
from downloader.universal import download_url
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
DOC_EXTS   = {"pdf", "docx", "doc", "xlsx", "xls", "pptx", "zip", "rar", "7z"}

# ──────────── Progress Callback Factory ────────────
def make_progress_cb(client, chat_id, progress_msg_id, filename, action="dl"):
    last_edit = [0.0]
    async def cb(current, total, speed, elapsed):
        now = time.time()
        if now - last_edit[0] < Config.PROGRESS_UPDATE_INTERVAL:
            return
        last_edit[0] = now
        text = build_progress_text(action, current, total, speed, elapsed, filename)
        try:
            await client.edit_message_text(chat_id, progress_msg_id, text)
        except Exception:
            pass
    return cb

# ──────────── Upload Helper ────────────
async def smart_upload(client: Client, chat_id: int, file_path: str, info: dict, caption: str, thumb: str | None):
    ext  = (info.get("ext") or os.path.splitext(file_path)[1].lstrip(".")).lower()
    size = os.path.getsize(file_path)

    buttons = InlineKeyboardMarkup([[
        InlineKeyboardButton("👑 Owner", url=f"https://t.me/{Config.OWNER_USERNAME.strip('@')}"),
        InlineKeyboardButton("📞 Support", url=f"https://t.me/{Config.OWNER_USERNAME2.strip('@')}"),
    ]])

    if ext in VIDEO_EXTS:
        vinfo = await get_video_info(file_path)
        await client.send_video(
            chat_id,
            video=file_path,
            caption=caption,
            thumb=thumb,
            width=vinfo.get("width", 0),
            height=vinfo.get("height", 0),
            duration=int(vinfo.get("duration", 0)),
            supports_streaming=True,
            reply_markup=buttons,
        )
    elif ext in AUDIO_EXTS:
        await client.send_audio(
            chat_id,
            audio=file_path,
            caption=caption,
            thumb=thumb,
            title=info.get("title", ""),
            performer=info.get("uploader", ""),
            reply_markup=buttons,
        )
    elif ext in IMAGE_EXTS:
        await client.send_photo(
            chat_id,
            photo=file_path,
            caption=caption,
            reply_markup=buttons,
        )
    elif ext == "pdf":
        th = thumb or await extract_pdf_thumbnail(file_path, os.path.dirname(file_path))
        await client.send_document(
            chat_id,
            document=file_path,
            caption=caption,
            thumb=th,
            reply_markup=buttons,
        )
    else:
        await client.send_document(
            chat_id,
            document=file_path,
            caption=caption,
            thumb=thumb,
            reply_markup=buttons,
        )

# ──────────── Core Download + Upload Flow ────────────
async def process_single_url(client: Client, url: str, user_id: int, chat_id: int, reply_id: int):
    progress_msg = await client.send_message(
        chat_id,
        f"»»──── 🔍 Analyzing... ────««\n\n`{url[:60]}`",
        reply_to_message_id=reply_id
    )
    prog_id = progress_msg.id

    try:
        url_type = detect_url_type(url)
        start = time.time()

        # Download with progress
        dl_cb = make_progress_cb(client, chat_id, prog_id, url.split("/")[-1][:30], "dl")
        info  = await download_url(url, user_id, progress_cb=dl_cb)

        if not info.get("path") or not os.path.exists(info["path"]):
            raise RuntimeError("Download failed — file not found after download")

        file_path = info["path"]
        file_size = os.path.getsize(file_path)
        ext       = (info.get("ext") or os.path.splitext(file_path)[1].lstrip(".")).lower()
        title     = info.get("title", os.path.basename(file_path))

        # Check size
        if file_size > Config.MAX_FILE_SIZE:
            await client.edit_message_text(chat_id, prog_id,
                f"»»──── ❌ File Too Large ────««\n\n"
                f"File size: **{file_size // 1024 // 1024} MB**\n"
                f"Max allowed: **{Config.MAX_FILE_SIZE // 1024 // 1024} MB**"
            )
            cleanup(file_path)
            return

        # Fix video for Telegram streaming
        if ext in VIDEO_EXTS:
            await client.edit_message_text(chat_id, prog_id,
                "»»── 🔧 Processing video... ──««\n_(Making Telegram-playable…)_")
            file_path = await make_telegram_streamable(file_path)

        # Thumbnail
        out_dir = os.path.dirname(file_path)
        thumb = info.get("thumbnail")
        if not thumb and ext in VIDEO_EXTS:
            thumb = await extract_video_thumbnail(file_path, out_dir)
        elif not thumb and ext == "pdf":
            thumb = await extract_pdf_thumbnail(file_path, out_dir)
        if thumb:
            thumb = await prepare_thumbnail(thumb)

        # Inject metadata
        if ext in VIDEO_EXTS:
            file_path = await inject_video_metadata(
                file_path, title,
                artist=info.get("uploader", ""),
                comment=f"Downloaded by {Config.BOT_NAME} | {format_datetime()}"
            )

        # Caption
        user = await db.get_user(user_id)
        uname = user.get("username") if user else ""
        me    = await client.get_me()
        caption = build_caption(
            title=title,
            file_size=file_size,
            url_type=url_type,
            user_id=user_id,
            username=uname,
            bot_username=me.username,
            uploader=info.get("uploader", ""),
            duration=info.get("duration", 0),
            download_date=format_datetime(),
        )

        # Upload with progress
        await client.edit_message_text(chat_id, prog_id,
            build_progress_text("up", 0, file_size, 0, 0, os.path.basename(file_path)))

        up_cb = make_progress_cb(client, chat_id, prog_id, os.path.basename(file_path), "up")
        # Use a background task to update progress during upload
        upload_task = asyncio.ensure_future(
            smart_upload(client, chat_id, file_path, info, caption, thumb)
        )

        # Fake upload progress updates (Pyrogram doesn't support upload cb easily)
        async def _up_progress():
            while not upload_task.done():
                await asyncio.sleep(Config.PROGRESS_UPDATE_INTERVAL)
                elapsed = time.time() - start
                await up_cb(0, file_size, 0, elapsed)

        prog_task = asyncio.ensure_future(_up_progress())
        await upload_task
        prog_task.cancel()

        elapsed = time.time() - start
        done_txt = build_done_text(
            os.path.basename(file_path), file_size,
            elapsed, file_size / elapsed if elapsed > 0 else 0
        )
        await client.edit_message_text(chat_id, prog_id, done_txt)

        # Log to channel
        if Config.LOG_CHANNEL:
            try:
                await client.forward_messages(Config.LOG_CHANNEL, chat_id, [prog_id])
            except Exception:
                pass

        # Update stats
        await db.increment_daily(user_id)
        await db.log_download(user_id, url, title, file_size, "done")

        # Cleanup
        cleanup(file_path)
        if thumb:
            cleanup(thumb)

    except asyncio.CancelledError:
        await client.edit_message_text(chat_id, prog_id,
            "»»──── ❌ Cancelled ────««\nDownload was cancelled.")
        raise
    except Exception as e:
        logger.error(f"Download error for {url}: {e}", exc_info=True)
        await client.edit_message_text(chat_id, prog_id,
            f"»»──── ❌ Failed ────««\n\n"
            f"Could not download:\n`{url[:60]}`\n\n"
            f"**Error:** `{str(e)[:200]}`\n\n"
            f"Contact {Config.OWNER_USERNAME} for help."
        )
        await db.log_download(user_id, url, "", 0, "failed")

# ──────────── Queue Wrapper ────────────
async def queue_and_process(client: Client, urls: list[str], user_id: int, chat_id: int, reply_id: int):
    for i, url in enumerate(urls):
        task = await queue_manager.add_task(user_id, url, reply_id, chat_id)
        pos  = queue_manager.get_position(task.task_id)
        total = queue_manager.queue_size()

        if pos > 1:
            q_msg = await client.send_message(
                chat_id,
                build_queue_text(pos, total, url.split("/")[-1][:30]),
                reply_to_message_id=reply_id
            )
            # Wait until this task is at front
            try:
                await asyncio.wait_for(task.future, timeout=Config.DOWNLOAD_TIMEOUT)
            except asyncio.TimeoutError:
                await client.edit_message_text(chat_id, q_msg.id,
                    "»»──── ⏰ Timed Out ────««\nQueue wait timed out.")
                continue
            except asyncio.CancelledError:
                await client.edit_message_text(chat_id, q_msg.id,
                    "»»──── ❌ Cancelled ────««")
                continue
            try:
                await q_msg.delete()
            except Exception:
                pass
        else:
            # Directly start
            task.future.set_result("start") if not task.future.done() else None

        if task.status == "cancelled":
            continue

        await process_single_url(client, url, user_id, chat_id, reply_id)
        await asyncio.sleep(0.5)  # small delay between downloads

# ──────────── Message Handler: URLs ────────────
@Client.on_message(
    filters.private & filters.text & ~filters.command(
        ["start","help","cancel","mystats","queue","status","plans","buy","settings",
         "givepremium","removepremium","ban","unban","broadcast","stats","users"]
    )
)
@check_ban
@force_subscribe
@check_limit
async def text_link_handler(client: Client, message: Message):
    text = message.text or ""
    urls = extract_urls_from_text(text)
    if not urls:
        await message.reply(
            "»»──── ℹ️ No URL found ────««\n\n"
            "Please send a **valid URL** or a **.txt file** with links.\n"
            "Type /help for more info.",
            quote=True
        )
        return
    user_id = message.from_user.id
    await message.reply(
        f"»»── 📋 {len(urls)} URL(s) queued ──««\n\n"
        f"Processing {'one by one' if len(urls) > 1 else 'now'}…",
        quote=True
    )
    asyncio.ensure_future(
        queue_and_process(client, urls, user_id, message.chat.id, message.id)
    )

# ──────────── Message Handler: TXT Files ────────────
@Client.on_message(filters.private & filters.document)
@check_ban
@force_subscribe
@check_limit
async def document_handler(client: Client, message: Message):
    doc = message.document
    # .txt file with links
    if doc and doc.file_name and doc.file_name.lower().endswith(".txt"):
        status_msg = await message.reply("»»── 📄 Reading your links file… ──««", quote=True)
        out_dir = temp_dir_for_user(message.from_user.id)
        txt_path = os.path.join(out_dir, "links.txt")
        await message.download(file_name=txt_path)
        with open(txt_path, "r", errors="ignore") as f:
            content = f.read()
        urls = extract_urls_from_text(content)
        if not urls:
            await client.edit_message_text(message.chat.id, status_msg.id,
                "»»──── ❌ No URLs found ────««\nYour .txt file has no valid URLs.")
            return
        await client.edit_message_text(message.chat.id, status_msg.id,
            f"»»── ✅ Found **{len(urls)} URLs** ──««\nQueuing all downloads…")
        asyncio.ensure_future(
            queue_and_process(client, urls, message.from_user.id, message.chat.id, message.id)
        )
    else:
        await message.reply(
            "»»──── ℹ️ Unsupported File ────««\n\n"
            "Currently only **.txt** files with links are supported.\n"
            "Send a text file containing one URL per line!",
            quote=True
        )

# ──────────── /cancel ────────────
@Client.on_message(filters.command("cancel") & filters.private)
async def cancel_cmd(client: Client, message: Message):
    uid   = message.from_user.id
    count = await queue_manager.cancel_user_tasks(uid)
    await message.reply(
        f"»»──── ❌ CANCELLED ────««\n\n"
        f"Cancelled **{count}** pending download(s).\n"
        f"Active downloads may still complete.\n\n"
        f"»»──────────────────────««",
        quote=True
    )

# ──────────── /queue ────────────
@Client.on_message(filters.command("queue") & filters.private)
async def queue_cmd(client: Client, message: Message):
    uid    = message.from_user.id
    active = queue_manager.get_user_active(uid)
    if not active:
        await message.reply(
            "»»──── 📋 QUEUE ────««\n\nYou have **no active** downloads in queue.",
            quote=True
        )
        return
    lines = [f"»»────── 📋 YOUR QUEUE ──────««\n"]
    for i, t in enumerate(active, 1):
        lines.append(f"  {i}. [{t.status.upper()}] `{t.url[:40]}`")
    lines.append(f"\n»»──────────────────────────««")
    await message.reply("\n".join(lines), quote=True)
