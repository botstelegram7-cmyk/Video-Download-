"""
╔══════════════════════════════════════════╗
║    📊  P R O G R E S S  B A R  U T I L     ║
╚══════════════════════════════════════════╝
"""
import math
from utils.helpers import human_size, human_time

def make_progress_bar(current: int, total: int, length: int = 15) -> str:
    if total <= 0:
        return "▰" * length
    pct    = current / total
    filled = math.floor(pct * length)
    empty  = length - filled
    return "▰" * filled + "▱" * empty

def build_progress_text(action: str, current: int, total: int,
                         speed: float, elapsed: float, filename: str = "") -> str:
    pct  = (current / total * 100) if total > 0 else 0
    eta  = (total - current) / speed if speed > 0 else 0
    bar  = make_progress_bar(current, total)
    fname = (filename[:26] + "…") if len(filename) > 26 else filename
    emoji = "⬇️" if action == "dl" else "⬆️"
    label = "Downloading" if action == "dl" else "Uploading"

    return (
        f"╔══════════════════════════════╗\n"
        f"║  {emoji} {label:<27}║\n"
        f"╠══════════════════════════════╣\n"
        f"║  📄 {fname:<26}║\n"
        f"╠══════════════════════════════╣\n"
        f"║  {bar}  ║\n"
        f"║  📶 {pct:>5.1f}%  |  🚀 {human_size(int(speed))}/s      ║\n"
        f"║  📦 {human_size(current):>9} / {human_size(total):<12}║\n"
        f"║  ⏱️  Elapsed: {human_time(elapsed):<16}║\n"
        f"║  ⏳ ETA:     {human_time(eta):<17}║\n"
        f"╚══════════════════════════════╝"
    )

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
