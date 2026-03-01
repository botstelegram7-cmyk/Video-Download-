"""
╔══════════════════════════════════════════╗
║       💾  D A T A B A S E  M A N A G E R     ║
╚══════════════════════════════════════════╝
"""
import aiosqlite
import asyncio
import logging
from datetime import datetime, timedelta
from config import Config

logger = logging.getLogger(__name__)

DB_PATH = Config.DATABASE_PATH

# ──────────── Schema ────────────
SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    user_id     INTEGER PRIMARY KEY,
    username    TEXT,
    full_name   TEXT,
    plan        TEXT DEFAULT 'free',
    plan_expiry TEXT,
    daily_count INTEGER DEFAULT 0,
    last_reset  TEXT,
    joined_at   TEXT,
    is_banned   INTEGER DEFAULT 0
);

CREATE TABLE IF NOT EXISTS downloads (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id     INTEGER,
    url         TEXT,
    file_name   TEXT,
    file_size   INTEGER,
    status      TEXT,
    created_at  TEXT
);

CREATE TABLE IF NOT EXISTS bot_stats (
    key   TEXT PRIMARY KEY,
    value TEXT
);
"""

async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.executescript(SCHEMA)
        await db.commit()
    logger.info("✅ Database initialized")

# ──────────── User CRUD ────────────
async def get_user(user_id: int) -> dict | None:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM users WHERE user_id=?", (user_id,)) as cur:
            row = await cur.fetchone()
            return dict(row) if row else None

async def upsert_user(user_id: int, username: str, full_name: str):
    now = datetime.now().isoformat()
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            INSERT INTO users (user_id, username, full_name, joined_at, last_reset)
            VALUES (?,?,?,?,?)
            ON CONFLICT(user_id) DO UPDATE SET
                username=excluded.username,
                full_name=excluded.full_name
        """, (user_id, username or "", full_name or "", now, now))
        await db.commit()

async def get_or_create_user(user_id: int, username: str, full_name: str) -> dict:
    await upsert_user(user_id, username, full_name)
    return await get_user(user_id)

async def set_plan(user_id: int, plan: str, days: int):
    expiry = (datetime.now() + timedelta(days=days)).isoformat()
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE users SET plan=?, plan_expiry=? WHERE user_id=?",
            (plan, expiry, user_id)
        )
        await db.commit()

async def remove_plan(user_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE users SET plan='free', plan_expiry=NULL WHERE user_id=?",
            (user_id,)
        )
        await db.commit()

async def ban_user(user_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE users SET is_banned=1 WHERE user_id=?", (user_id,))
        await db.commit()

async def unban_user(user_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE users SET is_banned=0 WHERE user_id=?", (user_id,))
        await db.commit()

# ──────────── Plan / Limit ────────────
async def check_and_reset_daily(user_id: int) -> dict:
    """Reset daily count if new day."""
    user = await get_user(user_id)
    if not user:
        return None
    today = datetime.now().date().isoformat()
    last_reset = (user.get("last_reset") or "")[:10]
    if last_reset != today:
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute(
                "UPDATE users SET daily_count=0, last_reset=? WHERE user_id=?",
                (datetime.now().isoformat(), user_id)
            )
            await db.commit()
        user["daily_count"] = 0
    return user

async def increment_daily(user_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE users SET daily_count=daily_count+1 WHERE user_id=?",
            (user_id,)
        )
        await db.commit()

async def get_user_limit(user: dict) -> tuple[int, int]:
    """Returns (used, limit)."""
    uid = user["user_id"]
    # check plan expiry
    plan = user.get("plan", "free")
    expiry = user.get("plan_expiry")
    if expiry and plan != "free":
        if datetime.now() > datetime.fromisoformat(expiry):
            await remove_plan(uid)
            plan = "free"
    if uid in Config.OWNER_IDS:
        limit = Config.OWNER_DAILY_LIMIT
    elif plan == "premium":
        limit = Config.PREMIUM_DAILY_LIMIT
    elif plan == "basic":
        limit = Config.BASIC_DAILY_LIMIT
    else:
        limit = Config.BASIC_DAILY_LIMIT
    return user.get("daily_count", 0), limit

# ──────────── Downloads Log ────────────
async def log_download(user_id: int, url: str, file_name: str, file_size: int, status: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO downloads (user_id,url,file_name,file_size,status,created_at) VALUES (?,?,?,?,?,?)",
            (user_id, url, file_name, file_size, status, datetime.now().isoformat())
        )
        await db.commit()

# ──────────── Stats ────────────
async def get_total_users() -> int:
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT COUNT(*) FROM users") as cur:
            row = await cur.fetchone()
            return row[0] if row else 0

async def get_total_downloads() -> int:
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT COUNT(*) FROM downloads WHERE status='done'") as cur:
            row = await cur.fetchone()
            return row[0] if row else 0

async def get_all_user_ids() -> list[int]:
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT user_id FROM users") as cur:
            rows = await cur.fetchall()
            return [r[0] for r in rows]

async def get_premium_users() -> list[dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM users WHERE plan IN ('basic','premium')") as cur:
            rows = await cur.fetchall()
            return [dict(r) for r in rows]
