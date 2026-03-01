"""
╔══════════════════════════════════════════╗
║   🎬  F I L E  P R O C E S S O R           ║
╚══════════════════════════════════════════╝
Handles: thumbnail gen, metadata injection, format fixes
"""
import os, asyncio, logging, time
from pathlib import Path
from PIL import Image
from config import Config
from utils.helpers import sanitize_filename, format_datetime, temp_dir_for_user

logger = logging.getLogger(__name__)

# ──────────── Thumbnail: Video ────────────
async def extract_video_thumbnail(video_path: str, out_dir: str, time_sec: float = 3.0) -> str | None:
    thumb_path = os.path.join(out_dir, "thumb.jpg")
    cmd = [
        "ffmpeg", "-y",
        "-ss", str(time_sec),
        "-i", video_path,
        "-vframes", "1",
        "-vf", "scale=320:-1",
        "-q:v", "2",
        thumb_path
    ]
    proc = await asyncio.create_subprocess_exec(*cmd,
        stdout=asyncio.subprocess.DEVNULL, stderr=asyncio.subprocess.DEVNULL)
    await proc.wait()
    if proc.returncode == 0 and os.path.exists(thumb_path):
        return thumb_path
    return None

# ──────────── Thumbnail: PDF ────────────
async def extract_pdf_thumbnail(pdf_path: str, out_dir: str) -> str | None:
    thumb_path = os.path.join(out_dir, "pdf_thumb.jpg")
    try:
        import fitz  # PyMuPDF
        doc = fitz.open(pdf_path)
        page = doc.load_page(0)
        pix  = page.get_pixmap(matrix=fitz.Matrix(2, 2))
        pix.save(thumb_path)
        doc.close()
        # Resize
        img = Image.open(thumb_path)
        img.thumbnail((320, 320))
        img.save(thumb_path, "JPEG")
        return thumb_path
    except ImportError:
        logger.warning("PyMuPDF not installed, skipping PDF thumbnail")
    except Exception as e:
        logger.warning(f"PDF thumbnail error: {e}")
    return None

# ──────────── Resize Thumbnail ────────────
async def prepare_thumbnail(thumb_path: str) -> str:
    """Ensure thumbnail is JPEG ≤ 200KB, 320px."""
    try:
        img = Image.open(thumb_path).convert("RGB")
        img.thumbnail((320, 320))
        img.save(thumb_path, "JPEG", quality=85, optimize=True)
    except Exception as e:
        logger.warning(f"Thumbnail prepare error: {e}")
    return thumb_path

# ──────────── Metadata Caption Builder ────────────
def build_caption(
    title: str,
    file_size: int,
    url_type: str,
    user_id: int = None,
    username: str = "",
    bot_username: str = "",
    uploader: str = "",
    duration: int = 0,
    download_date: str = "",
) -> str:
    from utils.helpers import human_size
    from utils.progress import human_size as hs

    dl_date = download_date or format_datetime()
    dl_by   = f"@{bot_username}" if bot_username else Config.BOT_NAME
    user_tag = f"@{username}" if username else f"#{user_id}"

    def human_dur(s):
        if not s: return "N/A"
        m, s = divmod(int(s), 60)
        h, m = divmod(m, 60)
        return f"{h:02d}:{m:02d}:{s:02d}" if h else f"{m:02d}:{s:02d}"

    caption = (
        f"»»──────── 📥 DOWNLOADED ────────««\n\n"
        f"📄 **Title**   : {title[:60]}\n"
        f"📦 **Size**    : {hs(file_size)}\n"
        f"🏷️  **Source**  : {url_type.upper()}\n"
    )
    if uploader:
        caption += f"👤 **Author**  : {uploader[:40]}\n"
    if duration:
        caption += f"⏱️  **Duration**: {human_dur(duration)}\n"
    caption += (
        f"📅 **Date**    : {dl_date}\n"
        f"👤 **User**    : {user_tag}\n"
        f"🤖 **Bot**     : {dl_by}\n\n"
        f"»»──────────────────────────────««"
    )
    return caption

# ──────────── Inject Metadata into MP4 ────────────
async def inject_video_metadata(video_path: str, title: str, artist: str = "", comment: str = "") -> str:
    out_path = video_path.replace(".mp4", "_meta.mp4")
    cmd = [
        "ffmpeg", "-y",
        "-i", video_path,
        "-c", "copy",
        "-metadata", f"title={title}",
        "-metadata", f"artist={artist}",
        "-metadata", f"comment={comment}",
        "-movflags", "+faststart",
        out_path
    ]
    proc = await asyncio.create_subprocess_exec(*cmd,
        stdout=asyncio.subprocess.DEVNULL, stderr=asyncio.subprocess.DEVNULL)
    await proc.wait()
    if proc.returncode == 0 and os.path.exists(out_path):
        os.remove(video_path)
        return out_path
    return video_path

# ──────────── Fix Video for Telegram Streaming ────────────
async def make_telegram_streamable(video_path: str) -> str:
    """Re-mux video to ensure it's Telegram-playable (H.264, AAC, faststart)."""
    out_path = video_path.replace(".mp4", "_tg.mp4")
    if not video_path.endswith(".mp4"):
        out_path = video_path + "_tg.mp4"

    cmd = [
        "ffmpeg", "-y",
        "-i", video_path,
        "-c:v", "libx264",
        "-preset", "fast",
        "-crf", "23",
        "-c:a", "aac",
        "-b:a", "128k",
        "-movflags", "+faststart",
        "-threads", "4",
        out_path
    ]
    proc = await asyncio.create_subprocess_exec(*cmd,
        stdout=asyncio.subprocess.DEVNULL, stderr=asyncio.subprocess.DEVNULL)
    await proc.wait()
    if proc.returncode == 0 and os.path.exists(out_path):
        os.remove(video_path)
        return out_path
    return video_path  # fallback original

# ──────────── Get Video Info ────────────
async def get_video_info(video_path: str) -> dict:
    """Get width, height, duration via ffprobe."""
    cmd = [
        "ffprobe", "-v", "quiet",
        "-print_format", "json",
        "-show_streams", "-show_format",
        video_path
    ]
    proc = await asyncio.create_subprocess_exec(*cmd,
        stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.DEVNULL)
    stdout, _ = await proc.communicate()
    if proc.returncode == 0:
        import json
        data = json.loads(stdout.decode())
        streams = data.get("streams", [])
        fmt     = data.get("format", {})
        for s in streams:
            if s.get("codec_type") == "video":
                return {
                    "width":    s.get("width", 0),
                    "height":   s.get("height", 0),
                    "duration": float(fmt.get("duration", 0)),
                }
    return {"width": 0, "height": 0, "duration": 0}
