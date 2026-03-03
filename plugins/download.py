"""
╔══════════════════════════════════════════════════════════╗
║   📥  DOWNLOAD  HANDLER                                  ║
║   text links · .txt bulk · /audio · /info · /queue       ║
╚══════════════════════════════════════════════════════════╝
"""
import os, asyncio, logging, time
from pyrogram import filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton as Btn
from client import app
from config import Config
import database as db
from utils.helpers import (
    extract_urls, url_type, user_dir, cleanup,
    fmt_size, fmt_dt, is_owner,
)
from utils.progress import dl_text, done_text, queue_text
from utils.decorators import guard
from downloader.core import download, fetch_info
from downloader.media import (
    video_thumb, pdf_thumb, prep_thumb,
    remux, add_meta, video_info, build_caption,
)
from queue_manager import queue

log = logging.getLogger(__name__)

VIDEO = {"mp4","mkv","avi","mov","webm","flv","ts","wmv","m4v"}
AUDIO = {"mp3","aac","flac","wav","ogg","m4a","opus"}
IMAGE = {"jpg","jpeg","png","gif","webp","bmp"}

_CMDS = [
    "start","help","ping","status","plans","buy","settings",
    "mystats","history","feedback","audio","info","queue","cancel",
    "givepremium","removepremium","ban","unban","broadcast",
    "stats","users","banned","restart",
]

# ─────────────────────────────────────────────────────
def _pcb(client, chat_id, msg_id, fname, action="dl"):
    last = [0.0]
    async def cb(cur, tot, spd, ela):
        now = time.time()
        if now - last[0] < Config.PROGRESS_IV: return
        last[0] = now
        try:
            await client.edit_message_text(
                chat_id, msg_id, dl_text(cur, tot, spd, ela, fname, action))
        except Exception: pass
    return cb

def _upload_btns() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([[
        Btn("👑 Owner",   url=f"https://t.me/{Config.OWNER_UNAME}"),
        Btn("📞 Support", url=f"https://t.me/{Config.SUPPORT_UNAME}"),
        Btn("🔔 Channel", url=Config.FSUB_LINK),
    ]])

async def _upload(client, chat_id, fpath, info, caption, thumb):
    """Send file in the correct Telegram type based on actual extension."""
    ext  = (info.get("ext") or os.path.splitext(fpath)[1].lstrip(".")).lower()
    kb   = _upload_btns()
    name = os.path.basename(fpath)
    log.info("Upload ext=%s size=%s thumb=%s", ext, fmt_size(os.path.getsize(fpath)), bool(thumb))

    if ext in VIDEO:
        vi = await video_info(fpath)
        await client.send_video(
            chat_id, video=fpath, caption=caption, thumb=thumb,
            width=vi["width"], height=vi["height"],
            duration=int(vi["duration"]),
            supports_streaming=True, reply_markup=kb,
        )
    elif ext in AUDIO:
        await client.send_audio(
            chat_id, audio=fpath, caption=caption, thumb=thumb,
            title=info.get("title",""), performer=info.get("uploader",""),
            reply_markup=kb,
        )
    elif ext in IMAGE:
        await client.send_photo(chat_id, photo=fpath, caption=caption, reply_markup=kb)
    elif ext == "pdf":
        th = thumb or await pdf_thumb(fpath, os.path.dirname(fpath))
        await client.send_document(
            chat_id, document=fpath, caption=caption, thumb=th, reply_markup=kb)
    else:
        # zip, rar, apk, exe, iso, dmg, docx … — send as document, keep filename
        await client.send_document(
            chat_id, document=fpath, caption=caption,
            thumb=thumb, reply_markup=kb, file_name=name,
        )

# ─────────────────────────────────────────────────────
async def _process(client, url: str, uid: int, chat_id: int,
                   reply_id: int, audio=False):
    pm  = await client.send_message(
        chat_id,
        "»»──── 🔍 Analyzing… ────««\n\n`" + url[:80] + "`",
        reply_to_message_id=reply_id,
    )
    pid = pm.id
    log.info("process uid=%s url=%s", uid, url[:60])

    try:
        utype = url_type(url)
        t0    = time.time()
        cb    = _pcb(client, chat_id, pid, url.split("/")[-1][:30])
        info  = await download(url, uid, cb=cb, audio=audio)

        fpath = info.get("path")
        if not fpath or not os.path.exists(fpath):
            raise RuntimeError("File not found after download.")

        size  = os.path.getsize(fpath)
        ext   = (info.get("ext") or os.path.splitext(fpath)[1].lstrip(".")).lower()
        title = info.get("title", os.path.basename(fpath))

        # Size guard
        if size > Config.MAX_SIZE:
            await client.edit_message_text(chat_id, pid,
                f"»»──── ❌ File Too Large ────««\n\n"
                f"Size : **{fmt_size(size)}**\n"
                f"Max  : **{fmt_size(Config.MAX_SIZE)}**"
            )
            cleanup(fpath); return

        # ── Video: remux for Telegram streaming + metadata ──
        if ext in VIDEO:
            await client.edit_message_text(chat_id, pid,
                "»»── 🔧 Processing video… ──««\n_(Making Telegram-streamable…)_")
            fpath = await remux(fpath)
            ext   = os.path.splitext(fpath)[1].lstrip(".")
            info["ext"] = ext
            fpath = await add_meta(fpath, title, info.get("uploader",""))

        outdir = os.path.dirname(fpath)

        # ── Thumbnail (video → ffmpeg frame, pdf → PyMuPDF first page) ──
        thumb = info.get("thumbnail")
        if not thumb and ext in VIDEO:
            thumb = await video_thumb(fpath, outdir)
        elif not thumb and ext == "pdf":
            thumb = await pdf_thumb(fpath, outdir)
        if thumb and os.path.exists(thumb):
            thumb = await prep_thumb(thumb)
        else:
            thumb = None

        # ── Caption ──────────────────────────────────────────
        user  = await db.get_user(uid)
        uname = (user or {}).get("username","")
        me    = await client.get_me()
        cap   = build_caption(
            title=title, size=size, utype=utype,
            uid=uid, uname=uname, bot_uname=me.username,
            uploader=info.get("uploader",""),
            duration=info.get("duration", 0),
        )

        # Upload progress placeholder
        await client.edit_message_text(chat_id, pid,
            dl_text(0, size, 0, 0, os.path.basename(fpath), "up"))

        await _upload(client, chat_id, fpath, info, cap, thumb)

        elapsed = time.time() - t0
        await client.edit_message_text(chat_id, pid,
            done_text(os.path.basename(fpath), size, elapsed,
                      size / elapsed if elapsed > 0 else 0))

        if Config.LOG_CHANNEL:
            try: await client.forward_messages(Config.LOG_CHANNEL, chat_id, [pid])
            except Exception: pass

        await db.add_daily(uid)
        await db.log_dl(uid, url, title, size, "done")
        cleanup(fpath)
        if thumb: cleanup(thumb)

    except asyncio.CancelledError:
        try: await client.edit_message_text(chat_id, pid, "»»──── ❌ Cancelled ────««")
        except: pass
        raise
    except Exception as e:
        log.error("process error [%s]: %s", url[:50], e, exc_info=True)
        try:
            await client.edit_message_text(chat_id, pid,
                "»»──── ❌ Failed ────««\n\n"
                f"`{url[:60]}`\n\n"
                f"**Error:** `{str(e)[:300]}`\n\n"
                f"Contact @{Config.OWNER_UNAME} if this persists."
            )
        except: pass
        await db.log_dl(uid, url, "", 0, "failed")

# ─────────────────────────────────────────────────────
async def _enqueue(client, urls: list, uid: int, chat_id: int,
                   reply_id: int, audio=False):
    for url in urls:
        task = await queue.add(uid, url, chat_id, reply_id)
        pos  = queue.position(task.task_id)

        if pos > 1:
            qm = await client.send_message(
                chat_id,
                queue_text(pos, queue.size(), url.split("/")[-1][:30]),
                reply_to_message_id=reply_id,
            )
            try:
                await asyncio.wait_for(task.future, timeout=Config.DL_TIMEOUT)
            except (asyncio.TimeoutError, asyncio.CancelledError):
                try: await client.edit_message_text(chat_id, qm.id, "»»──── ⏰ Timed Out ────««")
                except: pass
                continue
            try: await qm.delete()
            except: pass
        else:
            if not task.future.done(): task.future.set_result("go")

        if task.status == "cancelled": continue
        await _process(client, url, uid, chat_id, reply_id, audio=audio)
        await asyncio.sleep(0.3)

# ═══════════════════════════════════════════════════
#  /audio
# ═══════════════════════════════════════════════════
@app.on_message(filters.command("audio") & ~filters.outgoing)
@guard
async def cmd_audio(client, msg: Message):
    parts = msg.text.split(None, 1)
    if len(parts) < 2:
        await msg.reply(
            "»»──── 🎵 AUDIO DOWNLOAD ────««\n\n"
            "Usage: `/audio <URL>`\n\n"
            "Downloads **audio only** (MP3) from\n"
            "YouTube, TikTok, Instagram and more.\n\n"
            "»»──────────────────────────««",
            quote=True
        ); return
    urls = extract_urls(parts[1])
    if not urls:
        await msg.reply("No valid URL found.", quote=True); return
    await msg.reply(
        f"»»── 🎵 Audio queued ({len(urls)}) ──««\n\nProcessing…", quote=True)
    asyncio.ensure_future(
        _enqueue(client, urls, msg.from_user.id, msg.chat.id, msg.id, audio=True))

# ═══════════════════════════════════════════════════
#  /info
# ═══════════════════════════════════════════════════
@app.on_message(filters.command("info") & ~filters.outgoing)
@guard
async def cmd_info(client, msg: Message):
    parts = msg.text.split(None, 1)
    if len(parts) < 2:
        await msg.reply(
            "»»──── ℹ️ URL INFO ────««\n\nUsage: `/info <URL>`\n\n"
            "Gets info **without downloading**.\n\n»»──────────────────────────««",
            quote=True); return
    urls = extract_urls(parts[1])
    if not urls:
        await msg.reply("No valid URL found.", quote=True); return
    url  = urls[0]
    wait = await msg.reply("»»──── 🔍 Fetching info… ────««", quote=True)
    try:
        info  = await fetch_info(url)
        title = (info.get("title") or "Unknown")[:60]
        upl   = info.get("uploader","Unknown")
        dur   = info.get("duration", 0)
        views = info.get("view_count", 0) or 0
        src   = url_type(url).upper()
        def hms(s):
            if not s: return "N/A"
            m,s = divmod(int(s),60); h,m = divmod(m,60)
            return f"{h:02d}:{m:02d}:{s:02d}" if h else f"{m:02d}:{s:02d}"
        await wait.edit_text(
            "»»──────── ℹ️ URL INFO ────────««\n\n"
            f"📄 **Title**    : {title}\n"
            f"👤 **Uploader** : {upl}\n"
            f"🏷️  **Source**   : {src}\n"
            f"⏱️  **Duration** : {hms(dur)}\n"
            f"👁️  **Views**    : {views:,}\n\n"
            "»»──────────────────────────────««"
        )
    except Exception as e:
        await wait.edit_text(
            "»»──── ❌ Info Failed ────««\n\nError: `" + str(e)[:200] + "`")

# ═══════════════════════════════════════════════════
#  Text message handler — main download trigger
# ═══════════════════════════════════════════════════
@app.on_message(~filters.outgoing & filters.text & ~filters.command(_CMDS))
@guard
async def handle_text(client, msg: Message):
    urls = extract_urls(msg.text or "")
    if not urls:
        await msg.reply(
            "»»──── ℹ️ No URL Found ────««\n\n"
            "Send a **valid URL** or **.txt** file with links.\n"
            "/help for instructions.",
            quote=True); return
    await msg.reply(
        f"»»── 📋 {len(urls)} URL(s) queued ──««\n\nProcessing…", quote=True)
    asyncio.ensure_future(
        _enqueue(client, urls, msg.from_user.id, msg.chat.id, msg.id))

# ═══════════════════════════════════════════════════
#  Document — .txt bulk download
# ═══════════════════════════════════════════════════
@app.on_message(~filters.outgoing & filters.document)
@guard
async def handle_doc(client, msg: Message):
    doc = msg.document
    if not (doc and doc.file_name and doc.file_name.lower().endswith(".txt")):
        await msg.reply(
            "»»──── ℹ️ Unsupported File ────««\n\n"
            "Only **.txt** files with links are supported.", quote=True); return
    sm  = await msg.reply("»»── 📄 Reading links file… ──««", quote=True)
    out = user_dir(msg.from_user.id)
    txt = os.path.join(out, "links.txt")
    await msg.download(file_name=txt)
    with open(txt, "r", errors="ignore") as f:
        content = f.read()
    urls = extract_urls(content)
    if not urls:
        await sm.edit_text("»»──── ❌ No URLs Found ────««\n\nNo valid URLs in file."); return
    await sm.edit_text(f"»»── ✅ Found **{len(urls)} URLs** ──««\nQueuing all downloads…")
    asyncio.ensure_future(
        _enqueue(client, urls, msg.from_user.id, msg.chat.id, msg.id))

# ═══════════════════════════════════════════════════
#  /cancel  /queue
# ═══════════════════════════════════════════════════
@app.on_message(filters.command("cancel") & ~filters.outgoing)
async def cmd_cancel(client, msg: Message):
    n = await queue.cancel_user(msg.from_user.id)
    await msg.reply(f"»»──── ❌ CANCELLED ────««\n\nCancelled **{n}** task(s).", quote=True)

@app.on_message(filters.command("queue") & ~filters.outgoing)
async def cmd_queue(client, msg: Message):
    active = queue.user_active(msg.from_user.id)
    if not active:
        await msg.reply("»»──── 📋 QUEUE ────««\n\nNo active downloads.", quote=True); return
    lines = ["»»────── 📋 YOUR QUEUE ──────««\n"]
    for i, t in enumerate(active, 1):
        lines.append(f"  {i}. [{t.status.upper()}] `{t.url[:40]}`")
    lines.append("\n»»──────────────────────────««")
    await msg.reply("\n".join(lines), quote=True)
