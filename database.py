import os
import aiosqlite
from datetime import datetime, date
from config import DB_PATH

os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)


async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            user_id     INTEGER PRIMARY KEY,
            username    TEXT,
            full_name   TEXT,
            plan        TEXT    DEFAULT 'free',
            plan_expiry TEXT    DEFAULT '',
            daily_count INTEGER DEFAULT 0,
            last_reset  TEXT    DEFAULT '',
            joined_at   TEXT    DEFAULT '',
            is_banned   INTEGER DEFAULT 0
        );
        CREATE TABLE IF NOT EXISTS downloads (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id    INTEGER,
            url        TEXT,
            title      TEXT,
            file_size  INTEGER DEFAULT 0,
            status     TEXT    DEFAULT 'pending',
            created_at TEXT
        );
        CREATE TABLE IF NOT EXISTS feedback (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id    INTEGER,
            text       TEXT,
            created_at TEXT
        );
        """)
        await db.commit()


async def get_user(user_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM users WHERE user_id=?", (user_id,)) as cur:
            row = await cur.fetchone()
            return dict(row) if row else None


async def upsert_user(user_id: int, username: str = "", full_name: str = ""):
    now = datetime.utcnow().isoformat()
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            INSERT INTO users (user_id, username, full_name, joined_at, last_reset)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(user_id) DO UPDATE SET username=excluded.username, full_name=excluded.full_name
        """, (user_id, username or "", full_name or "", now, now))
        await db.commit()


async def check_and_reset_daily(user_id: int):
    user = await get_user(user_id)
    if not user:
        return user
    today = date.today().isoformat()
    if user.get("last_reset", "") != today:
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute(
                "UPDATE users SET daily_count=0, last_reset=? WHERE user_id=?",
                (today, user_id))
            await db.commit()
        user["daily_count"] = 0
        user["last_reset"] = today
    return user


async def increment_daily(user_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE users SET daily_count=daily_count+1 WHERE user_id=?", (user_id,))
        await db.commit()


async def set_plan(user_id: int, plan: str, expiry: str = ""):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE users SET plan=?, plan_expiry=? WHERE user_id=?", (plan, expiry, user_id))
        await db.commit()


async def check_plan_expiry(user_id: int):
    user = await get_user(user_id)
    if not user:
        return
    if user["plan"] in ("basic", "premium") and user.get("plan_expiry"):
        try:
            if datetime.utcnow() > datetime.fromisoformat(user["plan_expiry"]):
                await set_plan(user_id, "free", "")
        except Exception:
            pass


async def ban_user(user_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE users SET is_banned=1 WHERE user_id=?", (user_id,))
        await db.commit()


async def unban_user(user_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE users SET is_banned=0 WHERE user_id=?", (user_id,))
        await db.commit()


async def log_download(user_id: int, url: str, title: str, file_size: int, status: str):
    now = datetime.utcnow().isoformat()
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO downloads (user_id,url,title,file_size,status,created_at) VALUES (?,?,?,?,?,?)",
            (user_id, url, title, file_size, status, now))
        await db.commit()


async def get_history(user_id: int, limit: int = 10):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM downloads WHERE user_id=? AND status='done' ORDER BY id DESC LIMIT ?",
            (user_id, limit)) as cur:
            return [dict(r) for r in await cur.fetchall()]


async def save_feedback(user_id: int, text: str):
    now = datetime.utcnow().isoformat()
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("INSERT INTO feedback (user_id,text,created_at) VALUES (?,?,?)", (user_id, text, now))
        await db.commit()


async def get_stats():
    async with aiosqlite.connect(DB_PATH) as db:
        async def cnt(q): return (await (await db.execute(q)).fetchone())[0]
        return {
            "total_users":     await cnt("SELECT COUNT(*) FROM users"),
            "total_downloads": await cnt("SELECT COUNT(*) FROM downloads WHERE status='done'"),
            "premium_users":   await cnt("SELECT COUNT(*) FROM users WHERE plan IN ('basic','premium')"),
            "banned_users":    await cnt("SELECT COUNT(*) FROM users WHERE is_banned=1"),
        }


async def get_all_users():
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT user_id FROM users WHERE is_banned=0") as cur:
            return [r["user_id"] for r in await cur.fetchall()]


async def get_premium_users():
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM users WHERE plan IN ('basic','premium')") as cur:
            return [dict(r) for r in await cur.fetchall()]


async def get_banned_users():
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM users WHERE is_banned=1") as cur:
            return [dict(r) for r in await cur.fetchall()]
