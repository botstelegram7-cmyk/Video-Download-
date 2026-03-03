"""Utility helpers — URL detection, formatting, auth checks."""
import os, re, logging
from datetime import datetime
from config import Config

log = logging.getLogger(__name__)

# ── URL patterns ────────────────────────────────────────
_YT     = re.compile(r"(https?://)?(www\.)?(youtube\.com|youtu\.be|music\.youtube\.com)/\S+")
_IG     = re.compile(r"(https?://)?(www\.)?instagram\.com/\S+")
_TW     = re.compile(r"(https?://)?(www\.)?(twitter\.com|x\.com)/\S+")
_TT     = re.compile(r"(https?://)?(vm\.|www\.)?tiktok\.com/\S+")
_FB     = re.compile(r"(https?://)?(www\.)?(facebook\.com|fb\.watch)/\S+")
_GD     = re.compile(r"https?://(drive|docs)\.google\.com/\S+")
_TB     = re.compile(
    r"(https?://)?(www\.)?"
    r"(terabox|1024terabox|terafileshare|4funbox|mirrobox|nephobox"
    r"|freeterabox|outfile|momerybox|tibibox|sendcmb)\.(com|net)/\S+"
)
_M3U8   = re.compile(r"https?://\S+\.m3u8\S*", re.I)
_DVID   = re.compile(r"https?://\S+\.(mp4|mkv|avi|mov|webm|flv|ts|wmv|m4v)(\?\S+)?$", re.I)
_DAUD   = re.compile(r"https?://\S+\.(mp3|aac|flac|wav|ogg|m4a|opus)(\?\S+)?$", re.I)
_DIMG   = re.compile(r"https?://\S+\.(jpg|jpeg|png|gif|webp|bmp)(\?\S+)?$", re.I)
_DDOC   = re.compile(
    r"https?://\S+\.(pdf|docx?|xlsx?|pptx?|zip|rar|7z|tar\.gz"
    r"|apk|exe|dmg|iso|deb|rpm|msi|pkg|cab|tar|gz|bz2|xz)(\?\S+)?$",
    re.I
)
_URL    = re.compile(r"https?://[^\s]+")

def url_type(url: str) -> str:
    if _YT.search(url):   return "youtube"
    if _IG.search(url):   return "instagram"
    if _TW.search(url):   return "twitter"
    if _TT.search(url):   return "tiktok"
    if _FB.search(url):   return "facebook"
    if _GD.search(url):   return "gdrive"
    if _TB.search(url):   return "terabox"
    if _M3U8.search(url): return "m3u8"
    if _DVID.search(url): return "direct_video"
    if _DAUD.search(url): return "direct_audio"
    if _DIMG.search(url): return "direct_image"
    if _DDOC.search(url): return "direct_doc"
    return "yt_dlp"

def extract_urls(text: str) -> list[str]:
    return list(dict.fromkeys(_URL.findall(text)))

def safe_name(name: str) -> str:
    name = re.sub(r'[\\/*?:"<>|]', "_", name).strip(". ")
    return name[:200] or "download"

def unique_path(directory: str, filename: str) -> str:
    base, ext = os.path.splitext(filename)
    path, n   = os.path.join(directory, filename), 1
    while os.path.exists(path):
        path = os.path.join(directory, f"{base}_{n}{ext}")
        n += 1
    return path

def user_dir(user_id: int) -> str:
    d = os.path.join(Config.DL_DIR, str(user_id))
    os.makedirs(d, exist_ok=True)
    return d

def cleanup(path: str):
    try:
        if path and os.path.isfile(path):   os.remove(path)
        elif path and os.path.isdir(path):
            import shutil; shutil.rmtree(path, ignore_errors=True)
    except Exception as e:
        log.debug("Cleanup: %s", e)

def fmt_size(n: int) -> str:
    if not n: return "0 B"
    for u in ("B","KB","MB","GB","TB"):
        if n < 1024: return f"{n:.2f} {u}"
        n /= 1024
    return f"{n:.2f} PB"

def fmt_time(s: float) -> str:
    import math
    if s <= 0 or not math.isfinite(s): return "∞"
    s = int(s); m, s = divmod(s, 60); h, m = divmod(m, 60)
    if h: return f"{h}h {m}m {s}s"
    if m: return f"{m}m {s}s"
    return f"{s}s"

def fmt_dt(dt=None) -> str:
    return (dt or datetime.now()).strftime("%d %b %Y • %I:%M %p")

def plan_badge(plan: str) -> str:
    return {"free": "🆓 Free", "basic": "🥉 Basic", "premium": "💎 Premium"}.get(plan, "🆓 Free")

def is_owner(uid: int) -> bool:
    return uid in Config.OWNER_IDS

async def is_subbed(client, uid: int) -> bool:
    if not Config.FSUB_ID: return True
    try:
        m = await client.get_chat_member(Config.FSUB_ID, uid)
        return "left" not in str(m.status).lower() and "kicked" not in str(m.status).lower()
    except Exception as e:
        log.warning("Sub check failed (allowing): %s", e)
        return True

def gdrive_id(url: str) -> str | None:
    for pat in (r"/file/d/([a-zA-Z0-9_-]+)", r"[?&]id=([a-zA-Z0-9_-]+)", r"/d/([a-zA-Z0-9_-]+)"):
        m = re.search(pat, url)
        if m: return m.group(1)
    return None
