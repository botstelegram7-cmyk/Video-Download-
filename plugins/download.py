import os
import asyncio
import time
from pyrogram import Client, filters
from pyrogram.types import Message
from client import app
from utils.decorators import guard
from utils.helpers import extract_url, url_type, fmt_size, cleanup
from utils.progress import ProgressTracker, dl_text
import database as db
from downloader.core import download, get_info
from downloader.media import remux, video_thumb, pdf_thumb, build_caption
from queue_manager import QueueItem, enqueue, process_queue
from config import MAX_SIZE, LOG_CHANNEL

VIDEO_EXTS = {"mp4", "mkv", "avi", "mov", "webm", "flv", "ts", "wmv", "m4v"}
AUDIO_EXTS = {"mp3", "aac", "flac", "wav", "ogg", "m4a", "opus"}
IMAGE_EXTS = {"jpg", "jpeg", "png", "gif", "webp", "bmp"}

SKIP_CMDS  = {
    "start","help","ping","status","plans","mystats","history",
    "queue","cancel","settings","feedback","audio","info",
    "givepremium","removepremium","ban","unban","broadcast",
    "stats","users","banned","restart",
}


# ── URL handler ───────────────────────────────────────────────────────────────
@app.on_message(
    filters.text & ~filters.outgoing
    & ~filters.command(list(SKIP_CMDS))
)
@guard
async def url_handler(client: Client, msg: Message):
    url = extract_url(msg.text)
    if not url:
        return
    await _enqueue_download(client, msg, url, audio_only=False)


# ── /audio ────────────────────────────────────────────────────────────────────
@app.on_message(filters.command("audio") & ~filters.outgoing)
@guard
async def cmd_audio(client: Client, msg: Message):
    parts = msg.text.split(None, 1)
    if len(parts) < 2:
        await msg.reply("Usage: /audio <url>")
        return
    url = extract_url(parts[1])
    if not url:
        await msg.reply("❌ No valid URL found.")
        return
    await _enqueue_download(client, msg, url, audio_only=True)


# ── /info ─────────────────────────────────────────────────────────────────────
@app.on_message(filters.command("info") & ~filters.outgoing)
async def cmd_info(client: Client, msg: Message):
    parts = msg.text.split(None, 1)
    if len(parts) < 2:
        await msg.reply("Usage: /info <url>")
        return
    url = extract_url(parts[1])
    if not url:
        await msg.reply("❌ No valid URL.")
        return
    m = await msg.reply("»»──── 🔍 Fetching info… ────««")
    try:
        info = await get_info(url)
        dur  = int(info.get("duration") or 0)
        mm, ss = divmod(dur, 60)
        views  = f"{info.get('views', 0):,}"
        await m.edit(
            f"»»──── ℹ️ Media Info ────««\n\n"
            f"▸ Title    : {info['title'][:60]}\n"
            f"▸ Uploader : {info['uploader']}\n"
            f"▸ Duration : {mm}m {ss}s\n"
            f"▸ Views    : {views}\n\n"
            f"⋆｡° ✮ @Universal_DownloadBot ✮ °｡⋆"
        )
    except Exception as e:
        await m.edit(f"❌ Failed to fetch info:\n{e}")


# ── .txt bulk file ────────────────────────────────────────────────────────────
@app.on_message(filters.document & ~filters.outgoing)
@guard
async def txt_handler(client: Client, msg: Message):
    doc = msg.document
    if not (doc.file_name or "").lower().endswith(".txt"):
        return
    m    = await msg.reply("»»──── 📄 Reading URL list… ────««")
    path = await msg.download()
    try:
        with open(path, "r", errors="ignore") as f:
            urls = [ln.strip() for ln in f if ln.strip().startswith("http")]
    finally:
        cleanup(path)
    if not urls:
        await m.edit("❌ No URLs found in file.")
        return
    await m.edit(f"»»──── 🔄 Queuing {len(urls)} URLs… ────««")
    for url in urls:
        await _enqueue_download(client, msg, url, audio_only=False, silent=True)
    await m.edit(
        f"»»──── ✅ Queued {len(urls)} URLs ────««\n\n"
        f"▸ Processing in background!\n\n"
        f"⋆｡° ✮ @Universal_DownloadBot ✮ °｡⋆"
    )


# ── Enqueue helper ────────────────────────────────────────────────────────────
async def _enqueue_download(client, msg, url, audio_only, silent=False):
    item = QueueItem(
        user_id=msg.from_user.id,
        url=url,
        msg=msg,
        extra={"audio_only": audio_only, "client": client},
    )
    pos = await enqueue(item)
    if pos > 1 and not silent:
        await msg.reply(
            f"»»──── 🔄 Added to Queue ────««\n\n"
            f"▸ Position : #{pos}\n"
            f"▸ URL      : {url[:55]}\n\n"
            f"⋆｡° ✮ @Universal_DownloadBot ✮ °｡⋆"
        )
    asyncio.create_task(process_queue(msg.from_user.id, _processor))


# ── Download processor ────────────────────────────────────────────────────────
async def _processor(item: QueueItem):
    client     = item.extra["client"]
    audio_only = item.extra["audio_only"]
    msg        = item.msg
    uid        = item.user_id
    url        = item.url
    user       = await db.get_user(uid) or {}
    username   = user.get("username") or "user"
    plan       = user.get("plan") or "free"

    status_msg = await msg.reply(
        f"»»──── ⏳ Processing ────««\n\n"
        f"▸ {url[:60]}\n\n"
        f"⋆｡° ✮ @Universal_DownloadBot ✮ °｡⋆"
    )

    tracker   = ProgressTracker()
    last_edit = [0.0]

    def progress_hook(d):
        if d.get("status") != "downloading":
            return
        cur   = d.get("downloaded_bytes", 0)
        total = d.get("total_bytes") or d.get("total_bytes_estimate") or 1
        spd, eta = tracker.update(cur, total)
        now = time.time()
        if now - last_edit[0] > 3:
            last_edit[0] = now
            asyncio.get_event_loop().call_soon_threadsafe(
                asyncio.ensure_future,
                status_msg.edit(dl_text(cur, total, spd, eta))
            )

    try:
        result = await download(url, uid, audio_only=audio_only, progress_hook=progress_hook)
    except Exception as e:
        await status_msg.edit(
            f"»»──── ❌ Download Failed ────««\n\n▸ {e}\n\n⋆｡° ✮ @Universal_DownloadBot ✮ °｡⋆"
        )
        await db.log_download(uid, url, str(e), 0, "failed")
        return

    path  = result["path"]
    title = result["title"]
    ext   = result["ext"].lower()
    size  = result["size"]

    if size > MAX_SIZE:
        await status_msg.edit(
            f"»»──── ❌ File Too Large ────««\n\n"
            f"▸ Size : {fmt_size(size)}\n▸ Limit: {fmt_size(MAX_SIZE)}\n\n"
            f"⋆｡° ✮ @Universal_DownloadBot ✮ °｡⋆"
        )
        cleanup(path)
        await db.log_download(uid, url, title, size, "failed")
        return

    await status_msg.edit(
        f"»»──── ☁️ Uploading… ────««\n\n"
        f"▸ {title[:50]}\n▸ {fmt_size(size)}\n\n"
        f"⋆｡° ✮ @Universal_DownloadBot ✮ °｡⋆"
    )

    caption = build_caption(title, size, url, username, plan)
    thumb   = None

    try:
        if ext in VIDEO_EXTS:
            thumb = await video_thumb(path)
            remuxed = path.rsplit(".", 1)[0] + "_r.mp4"
            if await remux(path, remuxed):
                cleanup(path)
                path = remuxed
                size = os.path.getsize(path)
            await client.send_video(
                msg.chat.id, path,
                caption=caption, thumb=thumb, supports_streaming=True
            )

        elif ext in AUDIO_EXTS:
            await client.send_audio(msg.chat.id, path, caption=caption, title=title)

        elif ext in IMAGE_EXTS:
            await client.send_photo(msg.chat.id, path, caption=caption)

        elif ext == "pdf":
            thumb = await pdf_thumb(path)
            await client.send_document(msg.chat.id, path, caption=caption, thumb=thumb)

        else:
            await client.send_document(
                msg.chat.id, path,
                caption=caption,
                file_name=os.path.basename(path)   # preserve original extension
            )

    except Exception as e:
        await status_msg.edit(
            f"»»──── ❌ Upload Failed ────««\n\n▸ {e}\n\n⋆｡° ✮ @Universal_DownloadBot ✮ °｡⋆"
        )
        cleanup(path)
        if thumb:
            cleanup(thumb)
        await db.log_download(uid, url, title, size, "failed")
        return

    cleanup(path)
    if thumb:
        cleanup(thumb)
    await db.increment_daily(uid)
    await db.log_download(uid, url, title, size, "done")

    try:
        await status_msg.delete()
    except Exception:
        pass

    if LOG_CHANNEL:
        try:
            await client.send_message(
                LOG_CHANNEL,
                f"✅ Download\n▸ @{username} ({uid})\n▸ {url[:80]}\n▸ {fmt_size(size)}"
            )
        except Exception:
            pass
