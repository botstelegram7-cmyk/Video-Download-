"""
╔══════════════════════════════════════════╗
║   🎬  F I L E  P R O C E S S O R          ║
╚══════════════════════════════════════════╝
Handles: thumbnail, metadata, format fixes
"""
import os, asyncio, logging
from config import Config
from utils.helpers import human_size, format_datetime

logger = logging.getLogger(__name__)

async def extract_video_thumbnail(video_path, out_dir, time_sec=3.0):
    thumb_path = os.path.join(out_dir, "thumb.jpg")
    cmd = [
        "ffmpeg", "-y", "-ss", str(time_sec),
        "-i", video_path, "-vframes", "1",
        "-vf", "scale=320:-1", "-q:v", "2", thumb_path
    ]
    proc = await asyncio.create_subprocess_exec(*cmd,
        stdout=asyncio.subprocess.DEVNULL, stderr=asyncio.subprocess.DEVNULL)
    await proc.wait()
    return thumb_path if (proc.returncode == 0 and os.path.exists(thumb_path)) else None

async def extract_pdf_thumbnail(pdf_path, out_dir):
    thumb_path = os.path.join(out_dir, "pdf_thumb.jpg")
    try:
        import fitz
        doc  = fitz.open(pdf_path)
        page = doc.load_page(0)
        pix  = page.get_pixmap(matrix=fitz.Matrix(2, 2))
        pix.save(thumb_path)
        doc.close()
        from PIL import Image
        img = Image.open(thumb_path)
        img.thumbnail((320, 320))
        img.save(thumb_path, "JPEG")
        return thumb_path
    except ImportError:
        logger.warning("PyMuPDF not installed, skipping PDF thumbnail")
    except Exception as e:
        logger.warning("PDF thumbnail error: %s", e)
    return None

async def prepare_thumbnail(thumb_path):
    try:
        from PIL import Image
        img = Image.open(thumb_path).convert("RGB")
        img.thumbnail((320, 320))
        img.save(thumb_path, "JPEG", quality=85, optimize=True)
    except Exception as e:
        logger.warning("Thumbnail prepare error: %s", e)
    return thumb_path

def build_caption(title, file_size, url_type, user_id=None, username="",
                  bot_username="", uploader="", duration=0, download_date=""):
    dl_date  = download_date or format_datetime()
    dl_by    = "@" + bot_username if bot_username else Config.BOT_NAME
    user_tag = "@" + username if username else "#" + str(user_id)

    def human_dur(s):
        if not s: return "N/A"
        m, s = divmod(int(s), 60)
        h, m = divmod(m, 60)
        return ("%02d:%02d:%02d" % (h, m, s)) if h else ("%02d:%02d" % (m, s))

    caption = (
        "»»──────── 📥 DOWNLOADED ────────««\n\n"
        "📄 **Title**   : " + str(title)[:60] + "\n"
        "📦 **Size**    : " + human_size(file_size) + "\n"
        "🏷️  **Source**  : " + str(url_type).upper() + "\n"
    )
    if uploader:
        caption += "👤 **Author**  : " + str(uploader)[:40] + "\n"
    if duration:
        caption += "⏱️  **Duration**: " + human_dur(duration) + "\n"
    caption += (
        "📅 **Date**    : " + dl_date + "\n"
        "👤 **User**    : " + user_tag + "\n"
        "🤖 **Bot**     : " + dl_by + "\n\n"
        "»»──────────────────────────────««"
    )
    return caption

async def inject_video_metadata(video_path, title, artist="", comment=""):
    out_path = video_path.replace(".mp4", "_meta.mp4")
    cmd = [
        "ffmpeg", "-y", "-i", video_path,
        "-c", "copy",
        "-metadata", "title=" + title,
        "-metadata", "artist=" + artist,
        "-metadata", "comment=" + comment,
        "-movflags", "+faststart", out_path
    ]
    proc = await asyncio.create_subprocess_exec(*cmd,
        stdout=asyncio.subprocess.DEVNULL, stderr=asyncio.subprocess.DEVNULL)
    await proc.wait()
    if proc.returncode == 0 and os.path.exists(out_path):
        try: os.remove(video_path)
        except Exception: pass
        return out_path
    return video_path

async def make_telegram_streamable(video_path):
    """Re-mux to H.264/AAC with faststart for Telegram streaming."""
    out_path = video_path + "_tg.mp4"
    cmd = [
        "ffmpeg", "-y", "-i", video_path,
        "-c:v", "libx264", "-preset", "fast", "-crf", "23",
        "-c:a", "aac", "-b:a", "128k",
        "-movflags", "+faststart", "-threads", "4",
        out_path
    ]
    proc = await asyncio.create_subprocess_exec(*cmd,
        stdout=asyncio.subprocess.DEVNULL, stderr=asyncio.subprocess.DEVNULL)
    await proc.wait()
    if proc.returncode == 0 and os.path.exists(out_path):
        try: os.remove(video_path)
        except Exception: pass
        return out_path
    return video_path

async def get_video_info(video_path):
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
        data    = json.loads(stdout.decode())
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
