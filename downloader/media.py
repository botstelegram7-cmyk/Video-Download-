"""
╔══════════════════════════════════════════════════╗
║  🎬  MEDIA PROCESSING                            ║
║  Thumbnails (video + PDF) · Remux · Metadata     ║
╚══════════════════════════════════════════════════╝
"""
import os, asyncio, logging, json
from config import Config
from utils.helpers import fmt_size, fmt_dt

log = logging.getLogger(__name__)

# ══════════════════════════════════════════════════
#  VIDEO THUMBNAIL
#  Tries multiple timestamps to ensure a non-black frame.
#  Falls back to yt-dlp supplied thumbnail if ffmpeg fails.
# ══════════════════════════════════════════════════
async def video_thumb(path: str, outdir: str) -> str | None:
    dest = os.path.join(outdir, "thumb_video.jpg")

    # Try several seek positions (3s, 1s, 10s, 30s, 0.1s)
    for seek in ("3", "1", "10", "30", "0.1"):
        proc = await asyncio.create_subprocess_exec(
            "ffmpeg", "-y",
            "-ss", seek,
            "-i", path,
            "-vframes", "1",
            "-vf", "scale=320:-2",          # keep aspect ratio, width 320
            "-q:v", "2",
            dest,
            stdout=asyncio.subprocess.DEVNULL,
            stderr=asyncio.subprocess.DEVNULL,
        )
        await proc.wait()
        if proc.returncode == 0 and os.path.exists(dest) and os.path.getsize(dest) > 0:
            log.info("Video thumb OK (seek=%ss) → %s", seek, dest)
            await _resize(dest)
            return dest

    log.warning("video_thumb: all seeks failed for %s", path)
    return None


# ══════════════════════════════════════════════════
#  PDF THUMBNAIL
#  Page 1 rendered at 2× scale via PyMuPDF (fitz).
#  Falls back to a plain placeholder if fitz not installed.
# ══════════════════════════════════════════════════
async def pdf_thumb(path: str, outdir: str) -> str | None:
    dest = os.path.join(outdir, "thumb_pdf.jpg")

    def _render():
        try:
            import fitz  # PyMuPDF
            doc  = fitz.open(path)
            page = doc.load_page(0)
            mat  = fitz.Matrix(2.0, 2.0)   # 2× resolution
            pix  = page.get_pixmap(matrix=mat, alpha=False)
            pix.save(dest)
            doc.close()
            return True
        except ImportError:
            log.warning("PyMuPDF not installed — PDF thumbnail unavailable")
        except Exception as e:
            log.warning("pdf_thumb fitz: %s", e)
        return False

    loop = asyncio.get_event_loop()
    ok   = await loop.run_in_executor(None, _render)
    if ok and os.path.exists(dest) and os.path.getsize(dest) > 0:
        await _resize(dest)
        return dest
    return None


# ══════════════════════════════════════════════════
#  THUMBNAIL RESIZE / NORMALISE
#  Telegram wants JPEG ≤ 320×320 for best display.
# ══════════════════════════════════════════════════
async def _resize(path: str):
    try:
        from PIL import Image
        loop = asyncio.get_event_loop()
        def _do():
            img = Image.open(path).convert("RGB")
            img.thumbnail((320, 320), Image.LANCZOS)
            img.save(path, "JPEG", quality=88, optimize=True)
        await loop.run_in_executor(None, _do)
    except Exception as e:
        log.debug("_resize: %s", e)

async def prep_thumb(path: str) -> str:
    """Resize + validate an existing thumbnail file."""
    if not path or not os.path.exists(path) or os.path.getsize(path) == 0:
        return None
    await _resize(path)
    return path


# ══════════════════════════════════════════════════
#  VIDEO INFO (width / height / duration via ffprobe)
# ══════════════════════════════════════════════════
async def video_info(path: str) -> dict:
    proc = await asyncio.create_subprocess_exec(
        "ffprobe", "-v", "quiet",
        "-print_format", "json",
        "-show_streams", "-show_format",
        path,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.DEVNULL,
    )
    out, _ = await proc.communicate()
    if proc.returncode == 0:
        try:
            data = json.loads(out.decode())
            for s in data.get("streams", []):
                if s.get("codec_type") == "video":
                    return {
                        "width":    int(s.get("width",    0)),
                        "height":   int(s.get("height",   0)),
                        "duration": float(data.get("format", {}).get("duration", 0)),
                    }
        except Exception as e:
            log.debug("video_info parse: %s", e)
    return {"width": 0, "height": 0, "duration": 0}


# ══════════════════════════════════════════════════
#  REMUX — ensure H.264 + AAC + faststart
#  Required so Telegram shows an inline player.
# ══════════════════════════════════════════════════
async def remux(path: str) -> str:
    dest = path + "_tg.mp4"
    proc = await asyncio.create_subprocess_exec(
        "ffmpeg", "-y", "-i", path,
        "-c:v", "libx264", "-preset", "fast", "-crf", "23",
        "-c:a", "aac", "-b:a", "128k",
        "-movflags", "+faststart",
        "-threads", "4",
        dest,
        stdout=asyncio.subprocess.DEVNULL,
        stderr=asyncio.subprocess.DEVNULL,
    )
    await proc.wait()
    if proc.returncode == 0 and os.path.exists(dest) and os.path.getsize(dest) > 0:
        try: os.remove(path)
        except: pass
        return dest
    log.warning("remux failed for %s — using original", path)
    return path


# ══════════════════════════════════════════════════
#  METADATA INJECTION
# ══════════════════════════════════════════════════
async def add_meta(path: str, title: str, artist: str = "") -> str:
    dest = path.replace(".mp4", "_m.mp4")
    proc = await asyncio.create_subprocess_exec(
        "ffmpeg", "-y", "-i", path,
        "-c", "copy",
        "-metadata", f"title={title}",
        "-metadata", f"artist={artist}",
        "-metadata", f"comment=Downloaded by {Config.BOT_NAME}",
        "-movflags", "+faststart",
        dest,
        stdout=asyncio.subprocess.DEVNULL,
        stderr=asyncio.subprocess.DEVNULL,
    )
    await proc.wait()
    if proc.returncode == 0 and os.path.exists(dest) and os.path.getsize(dest) > 0:
        try: os.remove(path)
        except: pass
        return dest
    return path


# ══════════════════════════════════════════════════
#  CAPTION BUILDER
# ══════════════════════════════════════════════════
def build_caption(title, size, utype, uid, uname,
                  bot_uname, uploader="", duration=0) -> str:
    def hms(s):
        if not s: return "N/A"
        m, s = divmod(int(s), 60)
        h, m = divmod(m, 60)
        return f"{h:02d}:{m:02d}:{s:02d}" if h else f"{m:02d}:{s:02d}"

    tag = f"@{uname}" if uname else f"#{uid}"
    c   = (
        "»»──────── 📥 DOWNLOADED ────────««\n\n"
        f"📄 **Title**    : {str(title)[:55]}\n"
        f"📦 **Size**     : {fmt_size(size)}\n"
        f"🏷️  **Source**   : {utype.upper()}\n"
    )
    if uploader: c += f"👤 **Uploader** : {str(uploader)[:40]}\n"
    if duration: c += f"⏱️  **Duration** : {hms(duration)}\n"
    c += (
        f"📅 **Date**     : {fmt_dt()}\n"
        f"👤 **User**     : {tag}\n"
        f"🤖 **Bot**      : @{bot_uname}\n\n"
        "»»──────────────────────────────««"
    )
    return c
