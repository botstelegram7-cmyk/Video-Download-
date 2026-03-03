"""
╔══════════════════════════════════════════╗
║         🛠️  H E L P E R  U T I L S         ║
╚══════════════════════════════════════════╝
"""
import os, re, logging, asyncio, aiohttp
from datetime import datetime
from config import Config

logger = logging.getLogger(__name__)

# ──────────── URL Detection ────────────
YOUTUBE_REGEX   = re.compile(r"(https?://)?(www\.)?(youtube\.com|youtu\.be|music\.youtube\.com)/\S+")
INSTAGRAM_REGEX = re.compile(r"(https?://)?(www\.)?instagram\.com/\S+")
TWITTER_REGEX   = re.compile(r"(https?://)?(www\.)?(twitter\.com|x\.com)/\S+")
TIKTOK_REGEX    = re.compile(r"(https?://)?(www\.)?tiktok\.com/\S+")
FACEBOOK_REGEX  = re.compile(r"(https?://)?(www\.)?(facebook\.com|fb\.watch)/\S+")
TERABOX_REGEX   = re.compile(
    r"(https?://)?(www\.)?"
    r"(terabox|1024terabox|terafileshare|4funbox|mirrobox|nephobox|freeterabox|outfile|momerybox|tibibox|sendcmb)"
    r"\.(com|net)/\S+"
)
M3U8_REGEX      = re.compile(r"https?://\S+\.m3u8\S*", re.IGNORECASE)
HLS_REGEX       = re.compile(r"https?://\S+(m3u8|hls|stream)\S*", re.IGNORECASE)
DIRECT_VIDEO    = re.compile(r"https?://\S+\.(mp4|mkv|avi|mov|webm|flv|ts|wmv|m4v)(\?\S+)?$", re.IGNORECASE)
DIRECT_AUDIO    = re.compile(r"https?://\S+\.(mp3|aac|flac|wav|ogg|m4a|opus)(\?\S+)?$", re.IGNORECASE)
DIRECT_IMAGE    = re.compile(r"https?://\S+\.(jpg|jpeg|png|gif|webp|bmp)(\?\S+)?$", re.IGNORECASE)
DIRECT_DOC      = re.compile(r"https?://\S+\.(pdf|docx?|xlsx?|pptx?|zip|rar|7z|tar\.gz)(\?\S+)?$", re.IGNORECASE)
URL_REGEX       = re.compile(r"https?://[^\s]+")

def detect_url_type(url: str) -> str:
    if YOUTUBE_REGEX.search(url):   return "youtube"
    if INSTAGRAM_REGEX.search(url): return "instagram"
    if TWITTER_REGEX.search(url):   return "twitter"
    if TIKTOK_REGEX.search(url):    return "tiktok"
    if FACEBOOK_REGEX.search(url):  return "facebook"
    if TERABOX_REGEX.search(url):   return "terabox"
    if M3U8_REGEX.search(url):      return "m3u8"
    if HLS_REGEX.search(url):       return "hls"
    if DIRECT_VIDEO.search(url):    return "direct_video"
    if DIRECT_AUDIO.search(url):    return "direct_audio"
    if DIRECT_IMAGE.search(url):    return "direct_image"
    if DIRECT_DOC.search(url):      return "direct_doc"
    return "yt_dlp"  # fallback: try yt-dlp

def extract_urls_from_text(text: str) -> list:
    return list(set(URL_REGEX.findall(text)))

def sanitize_filename(name: str) -> str:
    name = re.sub(r'[\\/*?:"<>|]', "_", name)
    name = name.strip(". ")
    return name[:200] or "download"

def get_unique_path(directory: str, filename: str) -> str:
    base, ext = os.path.splitext(filename)
    path = os.path.join(directory, filename)
    counter = 1
    while os.path.exists(path):
        path = os.path.join(directory, f"{base}_{counter}{ext}")
        counter += 1
    return path

def temp_dir_for_user(user_id: int) -> str:
    d = os.path.join(Config.DOWNLOAD_DIR, str(user_id))
    os.makedirs(d, exist_ok=True)
    return d

def cleanup(path: str):
    try:
        if not path:
            return
        if os.path.isfile(path):
            os.remove(path)
        elif os.path.isdir(path):
            import shutil
            shutil.rmtree(path, ignore_errors=True)
    except Exception as e:
        logger.warning(f"Cleanup error: {e}")

def human_size(num: int) -> str:
    """Convert bytes to human-readable string."""
    if not num:
        return "0 B"
    for unit in ["B", "KB", "MB", "GB"]:
        if num < 1024.0:
            return f"{num:.2f} {unit}"
        num /= 1024.0
    return f"{num:.2f} TB"

def human_time(seconds: float) -> str:
    import math
    if seconds <= 0 or not math.isfinite(seconds):
        return "∞"
    s = int(seconds)
    m, s = divmod(s, 60)
    h, m = divmod(m, 60)
    if h:
        return f"{h}h {m}m {s}s"
    elif m:
        return f"{m}m {s}s"
    return f"{s}s"

def format_datetime(dt=None) -> str:
    return (dt or datetime.now()).strftime("%d %b %Y • %I:%M %p")

def now_str() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def is_owner(user_id: int) -> bool:
    return user_id in Config.OWNER_IDS

async def is_subscribed(client, user_id: int) -> bool:
    """
    Check if user has joined the force-sub channel.
    Works with both Pyrogram v1 (string status) and v2 (enum status).
    """
    if not Config.FORCE_SUB_CHANNEL_ID:
        return True
    try:
        member = await client.get_chat_member(Config.FORCE_SUB_CHANNEL_ID, user_id)
        # Pyrogram v2 uses ChatMemberStatus enum; v1 uses strings.
        status = str(member.status).lower()
        # banned/kicked/left → not subscribed
        if any(x in status for x in ["kicked", "banned", "left"]):
            return False
        return True
    except Exception as e:
        logger.warning(f"Force sub check error (treating as subscribed): {e}")
        return True  # Don't block if check fails

def plan_badge(plan: str) -> str:
    return {
        "free":    "🆓 Free",
        "basic":   "🥉 Basic",
        "premium": "💎 Premium",
    }.get(plan, "🆓 Free")

async def get_file_size_from_url(url: str) -> int:
    try:
        async with aiohttp.ClientSession() as s:
            async with s.head(url, allow_redirects=True,
                              timeout=aiohttp.ClientTimeout(total=10)) as r:
                return int(r.headers.get("Content-Length", 0))
    except:
        return 0
