"""FFmpeg/Pillow media processing: thumbnails, metadata, remux, caption."""
import os, asyncio, logging, json
from config import Config
from utils.helpers import fmt_size, fmt_dt

log = logging.getLogger(__name__)

async def video_thumb(path: str, outdir: str, t: float = 3.0) -> str | None:
    dest = os.path.join(outdir, "thumb.jpg")
    proc = await asyncio.create_subprocess_exec(
        "ffmpeg", "-y", "-ss", str(t), "-i", path,
        "-vframes", "1", "-vf", "scale=320:-1", "-q:v", "2", dest,
        stdout=asyncio.subprocess.DEVNULL, stderr=asyncio.subprocess.DEVNULL
    )
    await proc.wait()
    return dest if (proc.returncode == 0 and os.path.exists(dest)) else None

async def pdf_thumb(path: str, outdir: str) -> str | None:
    dest = os.path.join(outdir, "pdf_thumb.jpg")
    try:
        import fitz
        doc  = fitz.open(path)
        page = doc.load_page(0)
        pix  = page.get_pixmap(matrix=fitz.Matrix(2, 2))
        pix.save(dest)
        doc.close()
        await _resize_thumb(dest)
        return dest
    except Exception as e:
        log.debug("PDF thumb: %s", e)
    return None

async def _resize_thumb(path: str):
    try:
        from PIL import Image
        img = Image.open(path).convert("RGB")
        img.thumbnail((320, 320))
        img.save(path, "JPEG", quality=85)
    except Exception as e:
        log.debug("Thumb resize: %s", e)

async def prep_thumb(path: str) -> str:
    await _resize_thumb(path)
    return path

async def video_info(path: str) -> dict:
    proc = await asyncio.create_subprocess_exec(
        "ffprobe", "-v", "quiet", "-print_format", "json",
        "-show_streams", "-show_format", path,
        stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.DEVNULL
    )
    out, _ = await proc.communicate()
    if proc.returncode == 0:
        data = json.loads(out.decode())
        for s in data.get("streams", []):
            if s.get("codec_type") == "video":
                return {
                    "width":    s.get("width", 0),
                    "height":   s.get("height", 0),
                    "duration": float(data.get("format", {}).get("duration", 0)),
                }
    return {"width": 0, "height": 0, "duration": 0}

async def remux(path: str) -> str:
    """Re-mux to H.264/AAC mp4 for Telegram streaming."""
    dest = path + "_tg.mp4"
    proc = await asyncio.create_subprocess_exec(
        "ffmpeg", "-y", "-i", path,
        "-c:v", "libx264", "-preset", "fast", "-crf", "23",
        "-c:a", "aac", "-b:a", "128k", "-movflags", "+faststart",
        "-threads", "4", dest,
        stdout=asyncio.subprocess.DEVNULL, stderr=asyncio.subprocess.DEVNULL
    )
    await proc.wait()
    if proc.returncode == 0 and os.path.exists(dest):
        try: os.remove(path)
        except: pass
        return dest
    return path

async def add_meta(path: str, title: str, artist: str = "") -> str:
    dest = path.replace(".mp4", "_m.mp4")
    proc = await asyncio.create_subprocess_exec(
        "ffmpeg", "-y", "-i", path,
        "-c", "copy",
        "-metadata", f"title={title}",
        "-metadata", f"artist={artist}",
        "-metadata", f"comment=Downloaded by {Config.BOT_NAME}",
        "-movflags", "+faststart", dest,
        stdout=asyncio.subprocess.DEVNULL, stderr=asyncio.subprocess.DEVNULL
    )
    await proc.wait()
    if proc.returncode == 0 and os.path.exists(dest):
        try: os.remove(path)
        except: pass
        return dest
    return path

def build_caption(title, size, utype, uid, uname, bot_uname, uploader="", duration=0) -> str:
    def hms(s):
        if not s: return "N/A"
        m, s = divmod(int(s), 60); h, m = divmod(m, 60)
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
