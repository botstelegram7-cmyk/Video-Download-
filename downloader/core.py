import os, asyncio, aiohttp, yt_dlp
from config import DL_DIR, MAX_SIZE
from utils.helpers import url_type, fmt_size

os.makedirs(DL_DIR, exist_ok=True)


def _cookie_file(name: str) -> str | None:
    path = f"/tmp/cookie_{name}.txt"
    return path if os.path.exists(path) else None


async def download(url: str, user_id: int,
                   audio_only: bool = False,
                   progress_hook=None) -> dict:
    """
    Universal download router.
    Returns: {"path": str, "title": str, "ext": str, "size": int}
    Raises:  Exception on failure
    """
    out_dir = os.path.join(DL_DIR, str(user_id))
    os.makedirs(out_dir, exist_ok=True)
    utype = url_type(url)

    if utype == "gdrive":
        return await _gdrive(url, out_dir)
    if utype == "terabox":
        return await _terabox(url, out_dir, progress_hook)
    if utype == "m3u8":
        return await _m3u8(url, out_dir)
    if utype in ("direct_video", "direct_audio", "direct_image", "direct_doc"):
        return await _direct(url, out_dir, progress_hook)

    # YouTube / Instagram / TikTok / Twitter / yt-dlp fallback
    return await _ytdlp(url, out_dir, audio_only, utype, progress_hook)


# ── yt-dlp ──────────────────────────────────────────────────────────────────
async def _ytdlp(url, out_dir, audio_only, utype, progress_hook):
    opts = {
        "outtmpl":          os.path.join(out_dir, "%(title).80s.%(ext)s"),
        "quiet":            True,
        "no_warnings":      True,
        "merge_output_format": "mp4",
    }
    if audio_only:
        opts["format"] = "bestaudio/best"
        opts["postprocessors"] = [{"key": "FFmpegExtractAudio", "preferredcodec": "mp3"}]

    # Cookies
    ck_map = {"youtube": "YT_COOKIES", "instagram": "INSTAGRAM_COOKIES", "terabox": "TERABOX_COOKIES"}
    ck_env = ck_map.get(utype, "")
    ck = _cookie_file(ck_env) if ck_env else None
    if ck:
        opts["cookiefile"] = ck

    if progress_hook:
        opts["progress_hooks"] = [progress_hook]

    def _do():
        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(url, download=True)
            return info

    info = await asyncio.get_event_loop().run_in_executor(None, _do)
    title = info.get("title", "Download")
    path  = yt_dlp.YoutubeDL(opts).prepare_filename(info)
    # Handle audio conversion extension change
    if audio_only:
        path = os.path.splitext(path)[0] + ".mp3"
    if not os.path.exists(path):
        # search for any file yt-dlp left
        files = os.listdir(out_dir)
        if files:
            path = os.path.join(out_dir, sorted(files)[-1])
    size = os.path.getsize(path) if os.path.exists(path) else 0
    ext  = os.path.splitext(path)[1].lstrip(".")
    return {"path": path, "title": title, "ext": ext, "size": size}


# ── Google Drive ─────────────────────────────────────────────────────────────
async def _gdrive(url, out_dir):
    import gdown
    def _do():
        return gdown.download(url, output=out_dir + "/", quiet=True, fuzzy=True)
    path = await asyncio.get_event_loop().run_in_executor(None, _do)
    if not path or not os.path.exists(path):
        raise Exception("Google Drive download failed.")
    return {"path": path, "title": os.path.basename(path), "ext": os.path.splitext(path)[1].lstrip("."), "size": os.path.getsize(path)}


# ── Terabox ──────────────────────────────────────────────────────────────────
async def _terabox(url, out_dir, progress_hook):
    # Try yt-dlp first
    try:
        return await _ytdlp(url, out_dir, False, "terabox", progress_hook)
    except Exception:
        pass
    # API fallback
    async with aiohttp.ClientSession() as sess:
        api_url = f"https://teraboxapp.com/api/download?url={url}"
        async with sess.get(api_url, timeout=aiohttp.ClientTimeout(total=30)) as r:
            data = await r.json()
        dl_url = data.get("download_link") or data.get("url")
        if not dl_url:
            raise Exception("Terabox API returned no link.")
        return await _direct(dl_url, out_dir, progress_hook)


# ── M3U8 / HLS ───────────────────────────────────────────────────────────────
async def _m3u8(url, out_dir):
    out_path = os.path.join(out_dir, "stream.mp4")
    cmd = ["ffmpeg", "-y", "-i", url, "-c", "copy", out_path]
    proc = await asyncio.create_subprocess_exec(*cmd,
                stdout=asyncio.subprocess.DEVNULL,
                stderr=asyncio.subprocess.DEVNULL)
    await proc.wait()
    if not os.path.exists(out_path):
        raise Exception("M3U8 stream download failed.")
    return {"path": out_path, "title": "HLS Stream", "ext": "mp4", "size": os.path.getsize(out_path)}


# ── Direct HTTP ───────────────────────────────────────────────────────────────
async def _direct(url, out_dir, progress_hook):
    async with aiohttp.ClientSession() as sess:
        async with sess.get(url, timeout=aiohttp.ClientTimeout(total=600)) as r:
            # Determine filename from Content-Disposition or URL
            cd  = r.headers.get("Content-Disposition", "")
            fname = None
            if "filename=" in cd:
                fname = cd.split("filename=")[-1].strip('"').strip("'")
            if not fname:
                fname = url.split("?")[0].split("/")[-1] or "download"
            path = os.path.join(out_dir, fname)
            total = int(r.headers.get("Content-Length", 0))
            if total > MAX_SIZE:
                raise Exception(f"File too large: {fmt_size(total)}")
            done = 0
            last_hook = 0
            with open(path, "wb") as f:
                async for chunk in r.content.iter_chunked(1024 * 512):
                    f.write(chunk)
                    done += len(chunk)
                    if progress_hook and (done - last_hook) > 1024 * 1024:
                        progress_hook({"status": "downloading", "downloaded_bytes": done, "total_bytes": total})
                        last_hook = done
    ext  = os.path.splitext(path)[1].lstrip(".")
    size = os.path.getsize(path)
    return {"path": path, "title": fname, "ext": ext, "size": size}


async def get_info(url: str) -> dict:
    """Fetch metadata without downloading."""
    def _do():
        with yt_dlp.YoutubeDL({"quiet": True, "no_warnings": True}) as ydl:
            return ydl.extract_info(url, download=False)
    info = await asyncio.get_event_loop().run_in_executor(None, _do)
    return {
        "title":    info.get("title", "Unknown"),
        "uploader": info.get("uploader", "Unknown"),
        "duration": info.get("duration", 0),
        "views":    info.get("view_count", 0),
        "thumbnail":info.get("thumbnail", ""),
    }
