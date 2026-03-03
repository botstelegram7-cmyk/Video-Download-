import time


def dl_text(current: int, total: int, speed: float, eta: int, title: str = "") -> str:
    pct = (current / total * 100) if total else 0
    filled = int(pct / 5)
    bar = "█" * filled + "░" * (20 - filled)
    size_done = _fmt(current)
    size_tot  = _fmt(total)
    spd       = _fmt(speed) + "/s"
    eta_str   = _eta(eta)
    header = f"»»──── ⬇️ Downloading ────««\n"
    if title:
        header += f"▸ {title[:50]}\n"
    return (
        f"{header}\n"
        f"[{bar}] {pct:.1f}%\n"
        f"▸ {size_done} / {size_tot}\n"
        f"▸ Speed : {spd}\n"
        f"▸ ETA   : {eta_str}\n"
        f"\n⋆｡° ✮ @Universal_DownloadBot ✮ °｡⋆"
    )


def _fmt(b: float) -> str:
    for unit in ("B", "KB", "MB", "GB"):
        if b < 1024:
            return f"{b:.1f} {unit}"
        b /= 1024
    return f"{b:.1f} TB"


def _eta(secs: int) -> str:
    if secs <= 0:
        return "—"
    m, s = divmod(secs, 60)
    h, m = divmod(m, 60)
    if h:
        return f"{h}h {m}m {s}s"
    if m:
        return f"{m}m {s}s"
    return f"{s}s"


class ProgressTracker:
    def __init__(self):
        self._start  = time.time()
        self._last   = time.time()
        self._last_b = 0

    def update(self, current: int, total: int) -> tuple:
        now   = time.time()
        dt    = now - self._last or 0.001
        speed = (current - self._last_b) / dt
        eta   = int((total - current) / speed) if speed > 0 else 0
        self._last   = now
        self._last_b = current
        return speed, eta
