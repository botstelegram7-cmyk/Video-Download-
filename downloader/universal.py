"""
╔══════════════════════════════════════════╗
║  🌐  U N I V E R S A L  D O W N L O A D E R ║
╚══════════════════════════════════════════╝
Supports: YouTube, Instagram, Twitter/X, TikTok,
          Facebook, Google Drive, Terabox, M3U8/HLS,
          Direct links (ANY extension), 1000+ sites
"""
import os, asyncio, logging, time, aiohttp, re
from config import Config
from utils.helpers import (
    sanitize_filename, get_unique_path, temp_dir_for_user, detect_url_type
)

logger = logging.getLogger(__name__)

# ──────────── Extract Google Drive file ID ────────────
def _extract_gdrive_id(url: str):
    patterns = [
        r"/file/d/([a-zA-Z0-9_-]+)",
        r"[?&]id=([a-zA-Z0-9_-]+)",
        r"/d/([a-zA-Z0-9_-]+)",
    ]
    for p in patterns:
        m = re.search(p, url)
        if m: return m.group(1)
    return None

# ──────────── YT-DLP progress hook ────────────
def make_ytdlp_hook(progress_cb):
    start = time.time()
    def hook(d):
        if d["status"] == "downloading":
            current = d.get("downloaded_bytes", 0)
            total   = d.get("total_bytes") or d.get("total_bytes_estimate") or 0
            speed   = d.get("speed") or 0
            elapsed = time.time() - start
            if progress_cb:
                try:
                    asyncio.get_event_loop().call_soon_threadsafe(
                        lambda: asyncio.ensure_future(
                            progress_cb(current, total, speed, elapsed)
                        )
                    )
                except Exception:
                    pass
    return hook

# ──────────── Cookie resolver ────────────
def get_cookie_path(url_type: str):
    mapping = {
        "youtube":   Config.YT_COOKIES_PATH,
        "instagram": Config.INSTAGRAM_COOKIES_PATH,
        "terabox":   Config.TERABOX_COOKIES_PATH,
    }
    path = mapping.get(url_type)
    return path if (path and os.path.exists(path)) else None

# ──────────── Info only (no download) ────────────
async def ytdlp_info_only(url: str) -> dict:
    import yt_dlp
    url_type    = detect_url_type(url)
    cookie_path = get_cookie_path(url_type)
    ydl_opts = {"quiet": True, "no_warnings": True, "skip_download": True}
    if cookie_path:
        ydl_opts["cookiefile"] = cookie_path
    loop = asyncio.get_event_loop()
    def _extract():
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            return ydl.extract_info(url, download=False)
    return await loop.run_in_executor(None, _extract)

# ──────────── YT-DLP Download ────────────
async def ytdlp_download(url: str, user_id: int, progress_cb=None, audio_only=False) -> dict:
    import yt_dlp
    out_dir     = temp_dir_for_user(user_id)
    url_type    = detect_url_type(url)
    cookie_path = get_cookie_path(url_type)

    if audio_only:
        ydl_opts = {
            "outtmpl":  os.path.join(out_dir, "%(title)s.%(ext)s"),
            "format":   "bestaudio/best",
            "postprocessors": [{
                "key":              "FFmpegExtractAudio",
                "preferredcodec":   "mp3",
                "preferredquality": "192",
            }],
            "quiet":       True,
            "no_warnings": True,
            "retries":     5,
        }
    else:
        ydl_opts = {
            "outtmpl":             os.path.join(out_dir, "%(title)s.%(ext)s"),
            "format":              "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best",
            "merge_output_format": "mp4",
            "writethumbnail":      True,
            "quiet":               True,
            "no_warnings":         True,
            "http_headers": {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
            },
            "retries":          5,
            "fragment_retries": 5,
            "postprocessors": [{
                "key":            "FFmpegVideoConvertor",
                "preferedformat": "mp4",
            }],
        }

    if cookie_path:
        ydl_opts["cookiefile"] = cookie_path
    if progress_cb:
        ydl_opts["progress_hooks"] = [make_ytdlp_hook(progress_cb)]

    loop = asyncio.get_event_loop()
    def _download():
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            return ydl.extract_info(url, download=True)

    info = await loop.run_in_executor(None, _download)
    title = info.get("title", "download")

    # Find downloaded file (newest media file)
    media_exts = (".mp4", ".mkv", ".webm", ".mp3", ".m4a", ".flac", ".opus", ".wav", ".aac")
    found = None
    try:
        files = sorted(
            [os.path.join(out_dir, f) for f in os.listdir(out_dir)
             if os.path.isfile(os.path.join(out_dir, f)) and f.lower().endswith(media_exts)],
            key=os.path.getmtime, reverse=True
        )
        if files:
            found = files[0]
    except Exception as e:
        logger.error("Finding downloaded file: %s", e)

    # Find thumbnail
    thumb = None
    try:
        for f in os.listdir(out_dir):
            if f.lower().endswith((".jpg", ".jpeg", ".png", ".webp")):
                thumb = os.path.join(out_dir, f)
                break
    except: pass

    return {
        "path":      found,
        "title":     title,
        "thumbnail": thumb,
        "duration":  info.get("duration", 0),
        "filesize":  os.path.getsize(found) if found else 0,
        "ext":       os.path.splitext(found)[1].lstrip(".") if found else info.get("ext", "mp4"),
        "url_type":  url_type,
        "uploader":  info.get("uploader", ""),
        "view_count": info.get("view_count", 0),
        "description": (info.get("description") or "")[:500],
    }

# ──────────── Direct Download (preserves original extension) ────────────
async def direct_download(url: str, user_id: int, progress_cb=None) -> dict:
    """
    Download any direct URL.
    Extension is ALWAYS preserved exactly as in the URL.
    zip → zip, apk → apk, mp4 → mp4, etc.
    """
    out_dir  = temp_dir_for_user(user_id)
    raw_name = url.split("?")[0].rstrip("/").split("/")[-1]
    if not raw_name or "." not in raw_name:
        raw_name = "download.bin"
    filename = sanitize_filename(raw_name)
    out_path = get_unique_path(out_dir, filename)
    ext      = os.path.splitext(filename)[1].lstrip(".")

    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    start   = time.time()

    async with aiohttp.ClientSession(headers=headers) as session:
        async with session.get(
            url,
            timeout=aiohttp.ClientTimeout(total=Config.DOWNLOAD_TIMEOUT),
            allow_redirects=True
        ) as resp:
            resp.raise_for_status()

            # Try to get filename from content-disposition
            cd = resp.headers.get("content-disposition", "")
            if "filename=" in cd:
                cd_name = cd.split("filename=")[-1].strip('" ')
                if cd_name and "." in cd_name:
                    filename = sanitize_filename(cd_name)
                    out_path = get_unique_path(out_dir, filename)
                    ext = os.path.splitext(filename)[1].lstrip(".")

            total   = int(resp.headers.get("Content-Length", 0))
            current = 0
            last_cb = 0
            with open(out_path, "wb") as f:
                async for chunk in resp.content.iter_chunked(1024 * 256):
                    f.write(chunk)
                    current += len(chunk)
                    now      = time.time()
                    elapsed  = now - start
                    speed    = current / elapsed if elapsed > 0 else 0
                    if progress_cb and (now - last_cb) >= Config.PROGRESS_UPDATE_INTERVAL:
                        await progress_cb(current, total, speed, elapsed)
                        last_cb = now

    size = os.path.getsize(out_path)
    return {
        "path":      out_path,
        "title":     os.path.splitext(filename)[0],
        "thumbnail": None,
        "filesize":  size,
        "ext":       ext,
        "url_type":  detect_url_type(url),
    }

# ──────────── Google Drive Download ────────────
async def gdrive_download(url: str, user_id: int, progress_cb=None) -> dict:
    """Download from Google Drive using gdown."""
    out_dir = temp_dir_for_user(user_id)
    file_id = _extract_gdrive_id(url)
    if not file_id:
        raise RuntimeError("Could not extract Google Drive file ID from URL")

    try:
        import gdown
    except ImportError:
        raise RuntimeError("gdown not installed. Add 'gdown' to requirements.txt")

    dl_url   = f"https://drive.google.com/uc?id={file_id}&export=download"
    out_path = os.path.join(out_dir, f"gdrive_{file_id}")

    loop = asyncio.get_event_loop()

    def _gdrive_dl():
        result = gdown.download(dl_url, out_path, quiet=False, fuzzy=True)
        if result is None:
            # Try folder download
            result = gdown.download_folder(url, output=out_dir, quiet=False)
        return result

    if progress_cb:
        await progress_cb(0, 0, 0, 0)

    result = await loop.run_in_executor(None, _gdrive_dl)

    if result is None or not os.path.exists(str(result)):
        raise RuntimeError("Google Drive download failed — file might be private or restricted")

    final_path = str(result)
    filename   = os.path.basename(final_path)
    ext        = os.path.splitext(filename)[1].lstrip(".")
    size       = os.path.getsize(final_path)

    return {
        "path":      final_path,
        "title":     os.path.splitext(filename)[0],
        "thumbnail": None,
        "filesize":  size,
        "ext":       ext,
        "url_type":  "gdrive",
    }

# ──────────── M3U8 / HLS Download ────────────
async def m3u8_download(url: str, user_id: int, progress_cb=None) -> dict:
    out_dir  = temp_dir_for_user(user_id)
    out_path = get_unique_path(out_dir, "stream.mp4")
    start    = time.time()
    cmd = [
        "ffmpeg", "-y",
        "-headers", "User-Agent: Mozilla/5.0",
        "-i", url,
        "-c", "copy",
        "-bsf:a", "aac_adtstoasc",
        "-movflags", "+faststart",
        out_path
    ]
    proc = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )
    if progress_cb:
        async def _fake_progress():
            while proc.returncode is None:
                await asyncio.sleep(Config.PROGRESS_UPDATE_INTERVAL)
                sz      = os.path.getsize(out_path) if os.path.exists(out_path) else 0
                elapsed = time.time() - start
                speed   = sz / elapsed if elapsed > 0 else 0
                await progress_cb(sz, 0, speed, elapsed)
        ptask = asyncio.ensure_future(_fake_progress())
    stdout, stderr = await proc.communicate()
    if progress_cb:
        ptask.cancel()
    if proc.returncode != 0:
        raise RuntimeError("ffmpeg M3U8 failed: " + stderr.decode()[-300:])
    return {
        "path":      out_path,
        "title":     "stream",
        "thumbnail": None,
        "filesize":  os.path.getsize(out_path),
        "ext":       "mp4",
        "url_type":  "m3u8",
    }

# ──────────── Terabox Download ────────────
async def terabox_download(url: str, user_id: int, progress_cb=None) -> dict:
    try:
        return await ytdlp_download(url, user_id, progress_cb)
    except Exception as e:
        logger.warning("yt-dlp terabox failed: %s, trying API…", e)
        return await _terabox_api(url, user_id, progress_cb)

async def _terabox_api(url: str, user_id: int, progress_cb=None) -> dict:
    api_url = (
        "https://teraboxapp.com/api/shorturlinfo?app_id=250528&web=1"
        "&channel=dubox&clienttype=0&shorturl=" + url
    )
    headers = {"User-Agent": "Mozilla/5.0", "Referer": "https://teraboxapp.com/"}
    async with aiohttp.ClientSession(headers=headers) as session:
        async with session.get(api_url) as resp:
            data = await resp.json(content_type=None)
    dlink = (data.get("list") or [{}])[0].get("dlink", "")
    if not dlink:
        raise RuntimeError("Could not extract Terabox download link")
    return await direct_download(dlink, user_id, progress_cb)

# ──────────── Master Router ────────────
async def download_url(url: str, user_id: int, progress_cb=None, audio_only=False) -> dict:
    url_type = detect_url_type(url)
    print(f"[DOWNLOAD] type={url_type} url={url[:80]}", flush=True)

    if url_type in ("m3u8", "hls"):
        return await m3u8_download(url, user_id, progress_cb)
    elif url_type == "gdrive":
        return await gdrive_download(url, user_id, progress_cb)
    elif url_type == "terabox":
        return await terabox_download(url, user_id, progress_cb)
    elif url_type in ("direct_video", "direct_audio", "direct_image", "direct_doc"):
        # ALWAYS use direct_download for these — preserves original extension!
        if audio_only:
            return await ytdlp_download(url, user_id, progress_cb, audio_only=True)
        return await direct_download(url, user_id, progress_cb)
    else:
        # youtube, instagram, twitter, tiktok, facebook, yt_dlp fallback
        return await ytdlp_download(url, user_id, progress_cb, audio_only=audio_only)
