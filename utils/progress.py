"""
╔══════════════════════════════════════════╗
║    📊  P R O G R E S S  B A R  U T I L      ║
╚══════════════════════════════════════════╝
"""
import time
import math

def make_progress_bar(current: int, total: int, length: int = 15) -> str:
    """Aesthetic progress bar with symbols."""
    if total <= 0:
        return "▰" * length
    pct = current / total
    filled = math.floor(pct * length)
    empty  = length - filled
    # Filled: ▰ | Empty: ▱
    bar = "▰" * filled + "▱" * empty
    return bar

def human_size(num: int) -> str:
    """Convert bytes to human-readable."""
    for unit in ["B", "KB", "MB", "GB"]:
        if num < 1024:
            return f"{num:.2f} {unit}"
        num /= 1024
    return f"{num:.2f} TB"

def human_time(seconds: float) -> str:
    """Convert seconds to H:M:S or M:S."""
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

def build_progress_text(
    action: str,
    current: int,
    total: int,
    speed: float,
    elapsed: float,
    filename: str = ""
) -> str:
    """Build full aesthetic progress message."""
    pct = (current / total * 100) if total > 0 else 0
    eta = (total - current) / speed if speed > 0 else 0
    bar = make_progress_bar(current, total)

    fname = (filename[:30] + "…") if len(filename) > 30 else filename

    text = (
        f"╔══════════════════════════════╗\n"
        f"║  {'⬇️  Downloading' if action == 'dl' else '⬆️  Uploading':<28}║\n"
        f"╠══════════════════════════════╣\n"
        f"║  📄 {fname:<26}║\n"
        f"╠══════════════════════════════╣\n"
        f"║  {bar}  ║\n"
        f"║  📶 {pct:>5.1f}%  |  🚀 {human_size(int(speed))}/s{' ':>5}║\n"
        f"║  📦 {human_size(current):>9} / {human_size(total):<12}║\n"
        f"║  ⏱️  Elapsed: {human_time(elapsed):<16}║\n"
        f"║  ⏳ ETA:     {human_time(eta):<17}║\n"
        f"╚══════════════════════════════╝"
    )
    return text

def build_queue_text(position: int, total_in_queue: int, filename: str = "") -> str:
    fname = (filename[:28] + "…") if len(filename) > 28 else filename
    return (
        f"»»──────── ⏳ QUEUED ────────««\n"
        f"  📄 {fname}\n"
        f"  📍 Position : #{position} / {total_in_queue}\n"
        f"  ⌛ Please wait your turn…\n"
        f"»»──────────────────────────««"
    )

def build_done_text(filename: str, file_size: int, elapsed: float, avg_speed: float) -> str:
    fname = (filename[:28] + "…") if len(filename) > 28 else filename
    return (
        f"»»──────── ✅ DONE ──────────««\n"
        f"  📄 {fname}\n"
        f"  📦 Size   : {human_size(file_size)}\n"
        f"  ⚡ Speed  : {human_size(int(avg_speed))}/s\n"
        f"  ⏱  Time   : {human_time(elapsed)}\n"
        f"»»──────────────────────────««"
    )
