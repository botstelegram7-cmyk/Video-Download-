"""
╔══════════════════════════════════════════════════╗
║  🌐  UNIVERSAL DOWNLOADER                        ║
║  YouTube · Instagram · TikTok · Twitter          ║
║  Facebook · Google Drive · Terabox               ║
║  M3U8/HLS · Direct Links · 1000+ via yt-dlp     ║
╚══════════════════════════════════════════════════╝
"""
import os, asyncio, logging, time, aiohttp, re
from config import Config
from utils.helpers import safe_name, unique_path, user_dir, url_type, gdrive_id

log = logging.getLogger(__name__)

# ═══════════════════════════════════════════
#  YT-DLP helpers
# ═══════════════════════════════════════════
def _hook_factory(cb):
    t0 = time.time()
    def hook(d):
        if d["status"] != "downloading" or not cb: return
        cur = d.get("downloaded_bytes", 0)
        tot = d.get("total_bytes") or d.get("total_bytes_estimate") or 0
        spd = d.get("speed") or 0
        ela = time.time() - t0
        try:
            asyncio.get_event_loop().call_soon_threadsafe(
                lambda: asyncio.ensure_future(cb(cur, tot, spd, ela))
            )
        except Exception: pass
    return hook

def _cookie(utype: str) -> str | None:
    m = {"youtube": Config.YT_COOKIE, "instagram": Config.IG_COOKIE, "terabox": Config.TB_COOKIE}
    p = m.get(utype)
    return p if (p and os.path.exists(p)) else None

# ═══════════════════════════════════════════
#  Info-only (no download)
# ═══════════════════════════════════════════
async def fetch_info(url: str) -> dict:
    import yt_dlp
    utype = url_type(url)
    opts  = {"quiet": True, "no_warnings": True, "skip_download": True}
    ck    = _cookie(utype)
    if ck: opts["cookiefile"] = ck
    loop = asyncio.get_event_loop()
    def _run():
        with yt_dlp.YoutubeDL(opts) as ydl:
            return ydl.extract_info(url, download=False)
    return await loop.run_in_executor(None, _run)

# ═══════════════════════════════════════════
#  yt-dlp download
# ═══════════════════════════════════════════
async def _ytdlp(url: str, uid: int, cb=None, audio=False) -> dict:
    import yt_dlp
    out = user_dir(uid)
    utype = url_type(url)
    ck    = _cookie(utype)

    if audio:
        opts = {
            "outtmpl": os.path.join(out, "%(title)s.%(ext)s"),
            "format":  "bestaudio/best",
            "postprocessors": [{"key": "FFmpegExtractAudio",
                                "preferredcodec": "mp3", "preferredquality": "192"}],
            "quiet": True, "no_warnings": True, "retries": 5,
        }
    else:
        opts = {
            "outtmpl":             os.path.join(out, "%(title)s.%(ext)s"),
            "format":              "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best",
            "merge_output_format": "mp4",
            "writethumbnail":      True,
            "quiet":               True,
            "no_warnings":         True,
            "retries":             5,
            "fragment_retries":    5,
            "http_headers":        {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"},
            "postprocessors":      [{"key": "FFmpegVideoConvertor", "preferedformat": "mp4"}],
        }

    if ck:  opts["cookiefile"]    = ck
    if cb:  opts["progress_hooks"] = [_hook_factory(cb)]

    loop = asyncio.get_event_loop()
    info = await loop.run_in_executor(None, lambda: _dl_sync(url, opts))

    # Find newest media file
    MEDIA = (".mp4",".mkv",".webm",".mp3",".m4a",".flac",".opus",".wav",".aac")
    files = sorted(
        [os.path.join(out, f) for f in os.listdir(out)
         if os.path.isfile(os.path.join(out, f)) and f.lower().endswith(MEDIA)],
        key=os.path.getmtime, reverse=True
    )
    found = files[0] if files else None

    thumb = next(
        (os.path.join(out, f) for f in os.listdir(out)
         if f.lower().endswith((".jpg",".jpeg",".png",".webp"))),
        None
    )

    return {
        "path":      found,
        "title":     info.get("title", "download"),
        "thumbnail": thumb,
        "duration":  info.get("duration", 0),
        "uploader":  info.get("uploader", ""),
        "view_count":info.get("view_count", 0),
        "ext":       os.path.splitext(found)[1].lstrip(".") if found else "mp4",
        "filesize":  os.path.getsize(found) if found else 0,
        "url_type":  utype,
    }

def _dl_sync(url, opts):
    with __import__("yt_dlp").YoutubeDL(opts) as ydl:
        return ydl.extract_info(url, download=True)

# ═══════════════════════════════════════════
#  Direct HTTP download — preserves extension
# ═══════════════════════════════════════════
async def _direct(url: str, uid: int, cb=None) -> dict:
    out    = user_dir(uid)
    raw    = url.split("?")[0].rstrip("/").split("/")[-1]
    name   = safe_name(raw) if (raw and "." in raw) else "download.bin"
    path   = unique_path(out, name)
    ext    = os.path.splitext(name)[1].lstrip(".")
    hdrs   = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    t0     = time.time()

    async with aiohttp.ClientSession(headers=hdrs) as s:
        async with s.get(url, timeout=aiohttp.ClientTimeout(total=Config.DL_TIMEOUT),
                         allow_redirects=True) as r:
            r.raise_for_status()

            # Honour Content-Disposition filename
            cd = r.headers.get("content-disposition", "")
            if "filename=" in cd:
                cdn = re.search(r'filename="?([^";\n]+)', cd)
                if cdn:
                    better = safe_name(cdn.group(1).strip())
                    if "." in better:
                        name = better
                        path = unique_path(out, name)
                        ext  = os.path.splitext(name)[1].lstrip(".")

            tot, cur, last = int(r.headers.get("Content-Length", 0)), 0, 0.0
            with open(path, "wb") as f:
                async for chunk in r.content.iter_chunked(256 * 1024):
                    f.write(chunk)
                    cur += len(chunk)
                    now  = time.time()
                    if cb and (now - last) >= Config.PROGRESS_IV:
                        spd = cur / (now - t0) if (now - t0) > 0 else 0
                        await cb(cur, tot, spd, now - t0)
                        last = now

    return {
        "path":      path,
        "title":     os.path.splitext(name)[0],
        "thumbnail": None,
        "duration":  0,
        "uploader":  "",
        "ext":       ext,
        "filesize":  os.path.getsize(path),
        "url_type":  url_type(url),
    }

# ═══════════════════════════════════════════
#  Google Drive
# ═══════════════════════════════════════════
async def _gdrive(url: str, uid: int, cb=None) -> dict:
    try:
        import gdown
    except ImportError:
        raise RuntimeError("gdown not installed — add 'gdown' to requirements.txt")

    fid = gdrive_id(url)
    if not fid:
        raise RuntimeError("Cannot extract Google Drive file ID from URL")

    out  = user_dir(uid)
    dest = os.path.join(out, f"gdrive_{fid}")
    dl_url = f"https://drive.google.com/uc?id={fid}&export=download"

    if cb: await cb(0, 0, 0, 0)

    loop   = asyncio.get_event_loop()
    result = await loop.run_in_executor(
        None,
        lambda: gdown.download(dl_url, dest, quiet=False, fuzzy=True)
    )
    if not result or not os.path.exists(str(result)):
        raise RuntimeError("Google Drive download failed (file may be private/restricted)")

    fp   = str(result)
    name = os.path.basename(fp)
    return {
        "path":      fp,
        "title":     os.path.splitext(name)[0],
        "thumbnail": None,
        "duration":  0,
        "uploader":  "Google Drive",
        "ext":       os.path.splitext(name)[1].lstrip("."),
        "filesize":  os.path.getsize(fp),
        "url_type":  "gdrive",
    }

# ═══════════════════════════════════════════
#  M3U8 / HLS via ffmpeg
# ═══════════════════════════════════════════
async def _m3u8(url: str, uid: int, cb=None) -> dict:
    out  = user_dir(uid)
    dest = unique_path(out, "stream.mp4")
    t0   = time.time()
    cmd  = ["ffmpeg", "-y", "-headers", "User-Agent: Mozilla/5.0",
            "-i", url, "-c", "copy", "-bsf:a", "aac_adtstoasc",
            "-movflags", "+faststart", dest]
    proc = await asyncio.create_subprocess_exec(
        *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)

    if cb:
        async def _tick():
            while proc.returncode is None:
                await asyncio.sleep(Config.PROGRESS_IV)
                sz = os.path.getsize(dest) if os.path.exists(dest) else 0
                el = time.time() - t0
                await cb(sz, 0, sz / el if el > 0 else 0, el)
        tick = asyncio.ensure_future(_tick())

    _, stderr = await proc.communicate()
    if cb: tick.cancel()
    if proc.returncode != 0:
        raise RuntimeError("ffmpeg failed:\n" + stderr.decode()[-300:])

    return {"path": dest, "title": "stream", "thumbnail": None,
            "duration": 0, "uploader": "", "ext": "mp4",
            "filesize": os.path.getsize(dest), "url_type": "m3u8"}

# ═══════════════════════════════════════════
#  Terabox
# ═══════════════════════════════════════════
async def _terabox(url: str, uid: int, cb=None) -> dict:
    try:
        return await _ytdlp(url, uid, cb)
    except Exception as e:
        log.warning("yt-dlp terabox failed (%s), trying API…", e)
    # fallback API
    api = (
        "https://teraboxapp.com/api/shorturlinfo?app_id=250528&web=1"
        "&channel=dubox&clienttype=0&shorturl=" + url
    )
    hdrs = {"User-Agent": "Mozilla/5.0", "Referer": "https://teraboxapp.com/"}
    async with aiohttp.ClientSession(headers=hdrs) as s:
        async with s.get(api) as r:
            data = await r.json(content_type=None)
    dlink = (data.get("list") or [{}])[0].get("dlink", "")
    if not dlink:
        raise RuntimeError("Terabox: could not extract download link")
    return await _direct(dlink, uid, cb)

# ═══════════════════════════════════════════
#  Public router
# ═══════════════════════════════════════════
async def download(url: str, uid: int, cb=None, audio=False) -> dict:
    utype = url_type(url)
    log.info("DL [%s] %s", utype, url[:80])
    if utype == "m3u8":                          return await _m3u8(url, uid, cb)
    if utype == "gdrive":                        return await _gdrive(url, uid, cb)
    if utype == "terabox":                       return await _terabox(url, uid, cb)
    if utype in ("direct_video","direct_audio",
                 "direct_image","direct_doc"):
        if audio: return await _ytdlp(url, uid, cb, audio=True)
        return await _direct(url, uid, cb)
    return await _ytdlp(url, uid, cb, audio=audio)
