import os
import asyncio
import subprocess
from utils.helpers import fmt_size


def _run(cmd: list):
    return subprocess.run(cmd, capture_output=True, text=True)


async def remux(src: str, dst: str) -> bool:
    """Re-encode to H.264+AAC mp4 for Telegram inline streaming."""
    cmd = [
        "ffmpeg", "-y", "-i", src,
        "-c:v", "libx264", "-preset", "fast", "-crf", "22",
        "-c:a", "aac", "-b:a", "192k",
        "-movflags", "+faststart", dst,
    ]
    r = await asyncio.get_event_loop().run_in_executor(None, lambda: _run(cmd))
    return r.returncode == 0 and os.path.exists(dst)


async def video_thumb(video_path: str):
    """Try 5 seek positions to get a non-black thumbnail."""
    thumb = video_path + ".thumb.jpg"
    for seek in ("3", "1", "10", "30", "0.1"):
        cmd = ["ffmpeg", "-y", "-ss", seek, "-i", video_path,
               "-vframes", "1", "-vf", "scale=320:-1", thumb]
        r = await asyncio.get_event_loop().run_in_executor(None, lambda c=cmd: _run(c))
        if r.returncode == 0 and os.path.exists(thumb) and os.path.getsize(thumb) > 100:
            return thumb
    return None


async def pdf_thumb(pdf_path: str):
    """Extract page-1 from PDF as JPEG via PyMuPDF."""
    try:
        import fitz
        thumb = pdf_path + ".thumb.jpg"
        doc   = fitz.open(pdf_path)
        pix   = doc[0].get_pixmap(matrix=fitz.Matrix(2, 2))
        pix.save(thumb)
        doc.close()
        return thumb
    except Exception:
        return None


def build_caption(title: str, file_size: int, url: str, username: str, plan: str) -> str:
    badge    = {"basic": "🥉", "premium": "💎"}.get(plan, "🆓")
    safe_url = (url[:57] + "...") if len(url) > 60 else url
    return (
        f"»»──── ✅ Download Complete ────««\n\n"
        f"▸ Title  : {title[:60]}\n"
        f"▸ Size   : {fmt_size(file_size)}\n"
        f"▸ Source : {safe_url}\n"
        f"▸ User   : @{username} ({badge})\n\n"
        f"⋆｡° ✮ @Universal_DownloadBot ✮ °｡⋆"
    )
