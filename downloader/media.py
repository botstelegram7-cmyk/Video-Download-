import os, subprocess, asyncio
from config import DL_DIR


def _run(cmd: list) -> tuple:
    result = subprocess.run(cmd, capture_output=True, text=True)
    return result.returncode, result.stderr


async def remux(src: str, dst: str) -> bool:
    """Re-encode to H.264+AAC mp4 for Telegram streaming."""
    cmd = [
        "ffmpeg", "-y", "-i", src,
        "-c:v", "libx264", "-preset", "fast", "-crf", "22",
        "-c:a", "aac", "-b:a", "192k",
        "-movflags", "+faststart", dst
    ]
    rc, _ = await asyncio.get_event_loop().run_in_executor(None, lambda: _run(cmd))
    return rc == 0


async def add_meta(path: str, title: str = "", artist: str = "", comment: str = "") -> str:
    """Inject metadata via ffmpeg -c copy (no re-encode)."""
    tmp = path + ".meta.mp4"
    cmd = [
        "ffmpeg", "-y", "-i", path,
        "-c", "copy",
        "-metadata", f"title={title}",
        "-metadata", f"artist={artist}",
        "-metadata", f"comment={comment}",
        tmp
    ]
    rc, _ = await asyncio.get_event_loop().run_in_executor(None, lambda: _run(cmd))
    if rc == 0:
        os.replace(tmp, path)
    return path


async def video_thumb(video_path: str) -> str | None:
    """Extract video thumbnail trying 5 positions."""
    thumb = video_path + ".thumb.jpg"
    for seek in ("3", "1", "10", "30", "0.1"):
        cmd = [
            "ffmpeg", "-y", "-ss", seek,
            "-i", video_path, "-vframes", "1",
            "-vf", "scale=320:-1", thumb
        ]
        rc, _ = await asyncio.get_event_loop().run_in_executor(None, lambda: _run(cmd))
        if rc == 0 and os.path.exists(thumb) and os.path.getsize(thumb) > 0:
            return thumb
    return None


async def pdf_thumb(pdf_path: str) -> str | None:
    """Extract page-1 thumbnail from PDF using PyMuPDF."""
    try:
        import fitz
        thumb = pdf_path + ".thumb.jpg"
        doc = fitz.open(pdf_path)
        page = doc[0]
        mat = fitz.Matrix(2, 2)
        pix = page.get_pixmap(matrix=mat)
        pix.save(thumb)
        doc.close()
        return thumb
    except Exception:
        return None


def build_caption(title: str, file_size: int, url: str, username: str, plan: str) -> str:
    from utils.helpers import fmt_size
    badge = {"basic": "🥉", "premium": "💎", "free": "🆓"}.get(plan, "🆓")
    safe_url = url[:60] + "..." if len(url) > 60 else url
    return (
        f"»»──── ✅ Downloaded ────««\n\n"
        f"▸ Title  : {title[:60]}\n"
        f"▸ Size   : {fmt_size(file_size)}\n"
        f"▸ Source : {safe_url}\n"
        f"▸ User   : @{username} ({badge})\n\n"
        f"⋆｡° ✮ @Universal_DownloadBot ✮ °｡⋆"
    )
