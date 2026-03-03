"""Progress bar builder for download/upload messages."""
import math
from utils.helpers import fmt_size, fmt_time

def bar(cur: int, tot: int, length: int = 14) -> str:
    if tot <= 0: return "▰" * length
    f = math.floor((cur / tot) * length)
    return "▰" * f + "▱" * (length - f)

def dl_text(cur: int, tot: int, speed: float, elapsed: float, fname: str, action="dl") -> str:
    pct  = (cur / tot * 100) if tot > 0 else 0
    eta  = (tot - cur) / speed if speed > 0 else 0
    icon = "⬇️" if action == "dl" else "⬆️"
    name = (fname[:25] + "…") if len(fname) > 25 else fname
    return (
        f"╔══════════════════════════════╗\n"
        f"║  {icon}  {'Downloading' if action=='dl' else 'Uploading':<26}║\n"
        f"╠══════════════════════════════╣\n"
        f"║  📄 {name:<26}║\n"
        f"║  {bar(cur,tot):<14}  {pct:5.1f}%        ║\n"
        f"║  🚀 {fmt_size(int(speed))}/s  ⏱ {fmt_time(elapsed):<14}║\n"
        f"║  📦 {fmt_size(cur)} / {fmt_size(tot):<18}║\n"
        f"║  ⏳ ETA: {fmt_time(eta):<22}║\n"
        f"╚══════════════════════════════╝"
    )

def done_text(fname: str, size: int, elapsed: float, speed: float) -> str:
    name = (fname[:26] + "…") if len(fname) > 26 else fname
    return (
        f"»»────── ✅ DOWNLOADED ──────««\n\n"
        f"  📄 {name}\n"
        f"  📦 {fmt_size(size)}\n"
        f"  ⚡ {fmt_size(int(speed))}/s\n"
        f"  ⏱  {fmt_time(elapsed)}\n\n"
        f"»»──────────────────────────««"
    )

def queue_text(pos: int, total: int, fname: str = "") -> str:
    name = (fname[:26] + "…") if len(fname) > 26 else fname
    return (
        f"»»──────── ⏳ QUEUED ────────««\n\n"
        f"  📄 {name}\n"
        f"  📍 Position : #{pos} of {total}\n"
        f"  ⌛ Please wait your turn…\n\n"
        f"»»──────────────────────────««"
    )
