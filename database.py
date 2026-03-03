"""
╔══════════════════════════════════════════╗
║          💾  DATABASE  MANAGER           ║
╚══════════════════════════════════════════╝
"""
import aiosqlite, logging
from datetime import datetime, timedelta
from config import Config

log = logging.getLogger(__name__)
_DB = Config.DB_PATH

_SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    user_id     INTEGER PRIMARY KEY,
    username    TEXT    DEFAULT '',
    full_name   TEXT    DEFAULT '',
    plan        TEXT    DEFAULT 'free',
    plan_expiry TEXT,
    daily_count INTEGER DEFAULT 0,
    last_reset  TEXT    DEFAULT '',
    joined_at   TEXT    DEFAULT '',
    is_banned   INTEGER DEFAULT 0
);
CREATE TABLE IF NOT EXISTS downloads (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id     INTEGER,
    url         TEXT,
    title       TEXT    DEFAULT '',
    file_size   INTEGER DEFAULT 0,
    status      TEXT    DEFAULT 'pending',
    created_at  TEXT
);
CREATE TABLE IF NOT EXISTS feedback (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id     INTEGER,
    text        TEXT,
    created_at  TEXT
);
"""

async def init():
    async with aiosqlite.connect(_DB) as db:
        await db.executescript(_SCHEMA)
        await db.commit()
    log.info("DB ready: %s", _DB)

# ── helpers ─────────────────────────────────────────────
async def _get(user_id: int) -> dict | None:
    async with aiosqlite.connect(_DB) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM users WHERE user_id=?", (user_id,)) as c:
            row = await c.fetchone()
            return dict(row) if row else None

async def ensure_user(user_id: int, username: str, full_name: str) -> dict:
    now = datetime.now().isoformat()
    async with aiosqlite.connect(_DB) as db:
        await db.execute("""
            INSERT INTO users (user_id, username, full_name, joined_at, last_reset)
            VALUES (?,?,?,?,?)
            ON CONFLICT(user_id) DO UPDATE SET
                username  = excluded.username,
                full_name = excluded.full_name
        """, (user_id, username or "", full_name or "", now, now))
        await db.commit()
    return await _get(user_id)

async def get_user(user_id: int) -> dict | None:
    return await _get(user_id)

# ── daily quota ─────────────────────────────────────────
async def reset_if_new_day(user_id: int) -> dict | None:
    user = await _get(user_id)
    if not user: return None
    today = datetime.now().date().isoformat()
    if (user.get("last_reset") or "")[:10] != today:
        async with aiosqlite.connect(_DB) as db:
            await db.execute(
                "UPDATE users SET daily_count=0, last_reset=? WHERE user_id=?",
                (datetime.now().isoformat(), user_id)
            )
            await db.commit()
        user["daily_count"] = 0
    return user

async def get_limit(user: dict) -> tuple[int, int]:
    """Returns (used, limit)."""
    uid  = user["user_id"]
    plan = user.get("plan", "free")
    # auto-expire
    exp = user.get("plan_expiry")
    if exp and plan != "free":
        try:
            if datetime.now() > datetime.fromisoformat(exp):
                await set_plan(uid, "free", 0)
                plan = "free"
        except: pass

    if uid in Config.OWNER_IDS:      lim = Config.OWNER_LIMIT
    elif plan == "premium":           lim = Config.PREMIUM_LIMIT
    elif plan == "basic":             lim = Config.BASIC_LIMIT
    else:                             lim = Config.FREE_LIMIT

    return user.get("daily_count", 0), lim

async def add_daily(user_id: int):
    async with aiosqlite.connect(_DB) as db:
        await db.execute(
            "UPDATE users SET daily_count=daily_count+1 WHERE user_id=?", (user_id,))
        await db.commit()

# ── plan management ─────────────────────────────────────
async def set_plan(user_id: int, plan: str, days: int):
    expiry = (datetime.now() + timedelta(days=days)).isoformat() if days else None
    async with aiosqlite.connect(_DB) as db:
        await db.execute(
            "UPDATE users SET plan=?, plan_expiry=? WHERE user_id=?",
            (plan, expiry, user_id))
        await db.commit()

async def remove_plan(user_id: int):
    async with aiosqlite.connect(_DB) as db:
        await db.execute(
            "UPDATE users SET plan='free', plan_expiry=NULL WHERE user_id=?", (user_id,))
        await db.commit()

async def ban(user_id: int):
    async with aiosqlite.connect(_DB) as db:
        await db.execute("UPDATE users SET is_banned=1 WHERE user_id=?", (user_id,))
        await db.commit()

async def unban(user_id: int):
    async with aiosqlite.connect(_DB) as db:
        await db.execute("UPDATE users SET is_banned=0 WHERE user_id=?", (user_id,))
        await db.commit()

# ── logs / stats ─────────────────────────────────────────
async def log_dl(user_id: int, url: str, title: str, size: int, status: str):
    async with aiosqlite.connect(_DB) as db:
        await db.execute(
            "INSERT INTO downloads (user_id,url,title,file_size,status,created_at) VALUES(?,?,?,?,?,?)",
            (user_id, url, title, size, status, datetime.now().isoformat()))
        await db.commit()

async def get_history(user_id: int, n: int = 10) -> list[dict]:
    async with aiosqlite.connect(_DB) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM downloads WHERE user_id=? AND status='done' ORDER BY created_at DESC LIMIT ?",
            (user_id, n)
        ) as c:
            return [dict(r) for r in await c.fetchall()]

async def save_feedback(user_id: int, text: str):
    async with aiosqlite.connect(_DB) as db:
        await db.execute(
            "INSERT INTO feedback (user_id,text,created_at) VALUES(?,?,?)",
            (user_id, text, datetime.now().isoformat()))
        await db.commit()

async def total_users() -> int:
    async with aiosqlite.connect(_DB) as db:
        async with db.execute("SELECT COUNT(*) FROM users") as c:
            return (await c.fetchone())[0]

async def total_downloads() -> int:
    async with aiosqlite.connect(_DB) as db:
        async with db.execute("SELECT COUNT(*) FROM downloads WHERE status='done'") as c:
            return (await c.fetchone())[0]

async def all_user_ids() -> list[int]:
    async with aiosqlite.connect(_DB) as db:
        async with db.execute("SELECT user_id FROM users") as c:
            return [r[0] for r in await c.fetchall()]

async def premium_users() -> list[dict]:
    async with aiosqlite.connect(_DB) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM users WHERE plan!='free'") as c:
            return [dict(r) for r in await c.fetchall()]

async def banned_users() -> list[dict]:
    async with aiosqlite.connect(_DB) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM users WHERE is_banned=1") as c:
            return [dict(r) for r in await c.fetchall()]
