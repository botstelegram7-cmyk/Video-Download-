import re
import os
from datetime import datetime
from config import FSUB_ID, OWNER_IDS

YT_RE     = re.compile(r"(youtube\.com|youtu\.be|music\.youtube\.com)")
IG_RE     = re.compile(r"instagram\.com")
TT_RE     = re.compile(r"(tiktok\.com|vm\.tiktok\.com)")
TW_RE     = re.compile(r"(twitter\.com|x\.com)")
FB_RE     = re.compile(r"(facebook\.com|fb\.watch)")
GD_RE     = re.compile(r"(drive\.google\.com|docs\.google\.com)")
TB_RE     = re.compile(
    r"(terabox\.com|4funbox\.com|1024tera\.com|teraboxapp\.com|"
    r"mirrobox\.com|nephobox\.com|freeterabox\.com|momerybox\.com|"
    r"tibibox\.com|boxlen\.com)"
)
M3U8_RE   = re.compile(r"\.m3u8")
VIDEO_EXT = re.compile(r"\.(mp4|mkv|avi|mov|webm|flv|ts|wmv|m4v)$", re.I)
AUDIO_EXT = re.compile(r"\.(mp3|aac|flac|wav|ogg|m4a|opus)$", re.I)
IMAGE_EXT = re.compile(r"\.(jpg|jpeg|png|gif|webp|bmp)$", re.I)
DOC_EXT   = re.compile(r"\.(zip|rar|apk|exe|pdf|docx|iso|7z|tar|gz|dmg|deb)$", re.I)
URL_RE    = re.compile(r"https?://\S+")


def extract_url(text: str):
    m = URL_RE.search(text or "")
    return m.group(0) if m else None


def url_type(url: str) -> str:
    if YT_RE.search(url):      return "youtube"
    if IG_RE.search(url):      return "instagram"
    if TT_RE.search(url):      return "tiktok"
    if TW_RE.search(url):      return "twitter"
    if FB_RE.search(url):      return "facebook"
    if GD_RE.search(url):      return "gdrive"
    if TB_RE.search(url):      return "terabox"
    if M3U8_RE.search(url):    return "m3u8"
    if VIDEO_EXT.search(url):  return "direct_video"
    if AUDIO_EXT.search(url):  return "direct_audio"
    if IMAGE_EXT.search(url):  return "direct_image"
    if DOC_EXT.search(url):    return "direct_doc"
    return "ytdlp"


def fmt_size(b: int) -> str:
    for unit in ("B", "KB", "MB", "GB"):
        if b < 1024:
            return f"{b:.1f} {unit}"
        b /= 1024
    return f"{b:.1f} TB"


def fmt_dt(iso: str) -> str:
    try:
        return datetime.fromisoformat(iso).strftime("%Y-%m-%d %H:%M")
    except Exception:
        return iso or "—"


def is_owner(user_id: int) -> bool:
    return user_id in OWNER_IDS


async def is_subbed(client, user_id: int) -> bool:
    if not FSUB_ID:
        return True
    try:
        member = await client.get_chat_member(FSUB_ID, user_id)
        status = str(member.status).lower()
        return any(s in status for s in ("member", "administrator", "owner", "creator"))
    except Exception:
        return False


def cleanup(path: str):
    try:
        if os.path.isfile(path):
            os.remove(path)
        elif os.path.isdir(path):
            import shutil
            shutil.rmtree(path, ignore_errors=True)
    except Exception:
        pass
