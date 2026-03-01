"""
╔══════════════════════════════════════════╗
║   🌐  U N I V E R S A L  D O W N L O A D E R  ║
╚══════════════════════════════════════════╝
Supports: YouTube, Instagram, Terabox, M3U8/HLS,
          Direct links, and 1000+ sites via yt-dlp
"""
import os, asyncio, logging, time, aiohttp, re
from pathlib import Path
from config import Config
from utils.helpers import sanitize_filename, get_unique_path, temp_dir_for_user, detect_url_type

logger = logging.getLogger(__name__)

# ──────────── YT-DLP Progress Hook Factory ────────────
def make_ytdlp_hook(progress_cb):
    """Returns a yt-dlp progress hook that calls progress_cb(current, total, speed, elapsed)."""
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
                        lambda: asyncio.ensure_future(progress_cb(current, total, speed, elapsed))
                    )
                except Exception:
                    pass
    return hook

# ──────────── Cookie Path Resolver ────────────
def get_cookie_path(url_type: str) -> str | None:
    mapping = {
        "youtube":   Config.YT_COOKIES_PATH,
        "instagram": Config.INSTAGRAM_COOKIES_PATH,
        "terabox":   Config.TERABOX_COOKIES_PATH,
    }
    path = mapping.get(url_type)
    if path and os.path.exists(path):
        return path
    return None

# ──────────── YT-DLP Download ────────────
async def ytdlp_download(url: str, user_id: int, progress_cb=None) -> dict:
    """
    Download via yt-dlp. Returns dict with:
      path, title, thumbnail, duration, filesize, ext, url_type
    """
    import yt_dlp

    out_dir = temp_dir_for_user(user_id)
    url_type = detect_url_type(url)
    cookie_path = get_cookie_path(url_type)

    ydl_opts = {
        "outtmpl":          os.path.join(out_dir, "%(title)s.%(ext)s"),
        "format":           "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best",
        "merge_output_format": "mp4",
        "writethumbnail":   True,
        "writeinfojson":    False,
        "noplaylist":       True,
        "quiet":            True,
        "no_warnings":      True,
        "http_headers":     {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        },
        "retries":          5,
        "fragment_retries": 5,
        "postprocessors": [
            {
                "key":            "FFmpegVideoConvertor",
                "preferedformat": "mp4",
            }
        ],
    }

    if cookie_path:
        ydl_opts["cookiefile"] = cookie_path

    if progress_cb:
        ydl_opts["progress_hooks"] = [make_ytdlp_hook(progress_cb)]

    loop = asyncio.get_event_loop()

    def _download():
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            return info

    info = await loop.run_in_executor(None, _download)

    # Find downloaded file
    title  = info.get("title", "download")
    ext    = info.get("ext",   "mp4")
    filename = sanitize_filename(f"{title}.{ext}")
    # Try to find the actual file
    found = None
    for f in os.listdir(out_dir):
        fpath = os.path.join(out_dir, f)
        if os.path.isfile(fpath) and f.endswith((".mp4", ".mkv", ".webm", ".mp3", ".m4a", ".flac")):
            found = fpath
            break

    # Find thumbnail
    thumb = None
    for f in os.listdir(out_dir):
        if f.endswith((".jpg", ".jpeg", ".png", ".webp")):
            thumb = os.path.join(out_dir, f)
            break

    return {
        "path":      found,
        "title":     title,
        "thumbnail": thumb,
        "duration":  info.get("duration", 0),
        "filesize":  os.path.getsize(found) if found else 0,
        "ext":       ext,
        "url_type":  url_type,
        "uploader":  info.get("uploader", ""),
        "description": info.get("description", "")[:500],
        "upload_date": info.get("upload_date", ""),
    }

# ──────────── Direct Download (aiohttp) ────────────
async def direct_download(url: str, user_id: int, progress_cb=None) -> dict:
    """Download a direct URL with progress updates."""
    out_dir = temp_dir_for_user(user_id)

    # Derive filename from URL
    raw_name  = url.split("?")[0].rstrip("/").split("/")[-1]
    filename  = sanitize_filename(raw_name or "download")
    out_path  = get_unique_path(out_dir, filename)

    headers = {"User-Agent": "Mozilla/5.0"}
    start   = time.time()

    async with aiohttp.ClientSession(headers=headers) as session:
        async with session.get(url, timeout=aiohttp.ClientTimeout(total=Config.DOWNLOAD_TIMEOUT)) as resp:
            resp.raise_for_status()
            total    = int(resp.headers.get("Content-Length", 0))
            current  = 0
            last_cb  = 0

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
        "ext":       os.path.splitext(filename)[1].lstrip("."),
        "url_type":  detect_url_type(url),
    }

# ──────────── M3U8/HLS Download ────────────
async def m3u8_download(url: str, user_id: int, progress_cb=None) -> dict:
    """Download HLS/M3U8 stream using ffmpeg."""
    out_dir   = temp_dir_for_user(user_id)
    out_path  = get_unique_path(out_dir, "stream.mp4")
    start     = time.time()

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

    # Periodic progress simulation (ffmpeg doesn't give byte progress easily)
    if progress_cb:
        async def _fake_progress():
            while proc.returncode is None:
                await asyncio.sleep(Config.PROGRESS_UPDATE_INTERVAL)
                sz = os.path.getsize(out_path) if os.path.exists(out_path) else 0
                elapsed = time.time() - start
                speed = sz / elapsed if elapsed > 0 else 0
                await progress_cb(sz, 0, speed, elapsed)
        task = asyncio.ensure_future(_fake_progress())

    stdout, stderr = await proc.communicate()

    if progress_cb:
        task.cancel()

    if proc.returncode != 0:
        raise RuntimeError(f"ffmpeg failed:\n{stderr.decode()[-500:]}")

    size = os.path.getsize(out_path)
    return {
        "path":      out_path,
        "title":     "stream",
        "thumbnail": None,
        "filesize":  size,
        "ext":       "mp4",
        "url_type":  "m3u8",
    }

# ──────────── Terabox Download ────────────
async def terabox_download(url: str, user_id: int, progress_cb=None) -> dict:
    """
    Terabox via yt-dlp (with cookies). Falls back to API scraping.
    """
    try:
        return await ytdlp_download(url, user_id, progress_cb)
    except Exception as e:
        logger.warning(f"yt-dlp terabox failed: {e}, trying API…")
        # Attempt terabox API
        return await _terabox_api(url, user_id, progress_cb)

async def _terabox_api(url: str, user_id: int, progress_cb=None) -> dict:
    """Scrape terabox download link via public API."""
    api_url = f"https://teraboxapp.com/api/shorturlinfo?app_id=250528&web=1&channel=dubox&clienttype=0&jsToken=&dp-logid=&dp-callid=&tsNow=1683016476498&shorturl={url}"
    headers = {
        "User-Agent": "Mozilla/5.0",
        "Referer": "https://teraboxapp.com/",
    }
    cookie_path = Config.TERABOX_COOKIES_PATH
    cookies = {}
    if os.path.exists(cookie_path):
        with open(cookie_path) as f:
            for line in f:
                parts = line.strip().split("\t")
                if len(parts) >= 7:
                    cookies[parts[5]] = parts[6]

    async with aiohttp.ClientSession(headers=headers, cookies=cookies) as session:
        async with session.get(api_url) as resp:
            data = await resp.json(content_type=None)

    dlink = data.get("list", [{}])[0].get("dlink", "")
    if not dlink:
        raise RuntimeError("Could not extract Terabox download link")
    return await direct_download(dlink, user_id, progress_cb)

# ──────────── Master Download Router ────────────
async def download_url(url: str, user_id: int, progress_cb=None) -> dict:
    url_type = detect_url_type(url)
    logger.info(f"Download [{url_type}]: {url[:80]}")

    if url_type in ("m3u8", "hls"):
        return await m3u8_download(url, user_id, progress_cb)
    elif url_type == "terabox":
        return await terabox_download(url, user_id, progress_cb)
    elif url_type in ("direct_video", "direct_audio", "direct_image", "direct_doc"):
        return await direct_download(url, user_id, progress_cb)
    else:
        # youtube, instagram, yt_dlp fallback
        return await ytdlp_download(url, user_id, progress_cb)
