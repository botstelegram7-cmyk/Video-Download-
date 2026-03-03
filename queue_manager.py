"""Async task queue with per-user tracking and cancellation."""
import asyncio, uuid, time, logging
from dataclasses import dataclass, field
from typing import Optional
from config import Config

log = logging.getLogger(__name__)

@dataclass
class Task:
    task_id:  str
    user_id:  int
    url:      str
    chat_id:  int
    msg_id:   int
    status:   str = "queued"       # queued | running | done | failed | cancelled
    created:  float = field(default_factory=time.time)
    future:   Optional[asyncio.Future] = field(default=None, compare=False, repr=False)

class Queue:
    def __init__(self):
        self._q       = asyncio.Queue(maxsize=Config.QUEUE_SIZE)
        self._tasks   = {}          # task_id → Task
        self._by_user = {}          # user_id → [task_id]
        self._running = False
        self._lock    = asyncio.Lock()

    async def start(self):
        self._running = True
        asyncio.ensure_future(self._worker())
        log.info("Queue worker started")

    async def stop(self):
        self._running = False

    async def add(self, user_id, url, chat_id, msg_id) -> Task:
        tid    = str(uuid.uuid4())[:8]
        future = asyncio.get_event_loop().create_future()
        task   = Task(tid, user_id, url, chat_id, msg_id, future=future)
        async with self._lock:
            self._tasks[tid] = task
            self._by_user.setdefault(user_id, []).append(tid)
        await self._q.put(tid)
        return task

    def position(self, tid: str) -> int:
        try: return list(self._q._queue).index(tid) + 1
        except ValueError: return 0

    def size(self) -> int:
        return self._q.qsize()

    def user_active(self, uid: int) -> list[Task]:
        return [self._tasks[t] for t in self._by_user.get(uid, [])
                if t in self._tasks and self._tasks[t].status in ("queued","running")]

    async def cancel_user(self, uid: int) -> int:
        n = 0
        for tid in self._by_user.get(uid, []):
            t = self._tasks.get(tid)
            if t and t.status == "queued":
                t.status = "cancelled"
                if t.future and not t.future.done(): t.future.cancel()
                n += 1
        return n

    async def _worker(self):
        while self._running:
            try:
                tid = await asyncio.wait_for(self._q.get(), timeout=1.0)
            except asyncio.TimeoutError: continue
            except Exception as e: log.error("Queue err: %s", e); continue

            t = self._tasks.get(tid)
            if not t or t.status == "cancelled":
                self._q.task_done(); continue

            t.status = "running"
            try:
                if t.future and not t.future.done():
                    t.future.set_result("go")
            except Exception: pass
            finally:
                self._q.task_done()

queue = Queue()
