"""
╔══════════════════════════════════════════╗
║   📋  Q U E U E  M A N A G E R            ║
╚══════════════════════════════════════════╝
"""
import asyncio, logging, time, uuid
from dataclasses import dataclass, field
from typing import Optional
from config import Config

logger = logging.getLogger(__name__)

@dataclass
class DownloadTask:
    task_id:    str
    user_id:    int
    url:        str
    message_id: int
    chat_id:    int
    filename:   str = ""
    status:     str = "queued"
    created_at: float = field(default_factory=time.time)
    future:     Optional[asyncio.Future] = field(default=None, compare=False, repr=False)

class QueueManager:
    def __init__(self):
        self._queue        = asyncio.Queue(maxsize=Config.MAX_QUEUE_SIZE)
        self._tasks        = {}
        self._user_tasks   = {}
        self._worker_running = False
        self._lock         = asyncio.Lock()

    async def start(self):
        self._worker_running = True
        asyncio.ensure_future(self._worker())
        logger.info("Queue worker started")

    async def stop(self):
        self._worker_running = False

    async def add_task(self, user_id, url, message_id, chat_id, filename=""):
        task_id = str(uuid.uuid4())[:8]
        loop    = asyncio.get_event_loop()
        future  = loop.create_future()
        task    = DownloadTask(
            task_id=task_id, user_id=user_id, url=url,
            message_id=message_id, chat_id=chat_id,
            filename=filename, future=future,
        )
        async with self._lock:
            self._tasks[task_id] = task
            self._user_tasks.setdefault(user_id, []).append(task_id)
        await self._queue.put(task_id)
        return task

    def get_position(self, task_id):
        items = list(self._queue._queue)
        try:
            return items.index(task_id) + 1
        except ValueError:
            return 0

    def queue_size(self):
        return self._queue.qsize()

    def get_task(self, task_id):
        return self._tasks.get(task_id)

    async def cancel_user_tasks(self, user_id):
        ids   = self._user_tasks.get(user_id, [])
        count = 0
        for tid in ids:
            task = self._tasks.get(tid)
            if task and task.status == "queued":
                task.status = "cancelled"
                if task.future and not task.future.done():
                    task.future.cancel()
                count += 1
        return count

    def get_user_active(self, user_id):
        ids = self._user_tasks.get(user_id, [])
        return [
            self._tasks[tid]
            for tid in ids
            if tid in self._tasks and self._tasks[tid].status in ("queued", "downloading")
        ]

    async def _worker(self):
        while self._worker_running:
            try:
                task_id = await asyncio.wait_for(self._queue.get(), timeout=1.0)
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                logger.error("Queue worker error: %s", e)
                continue

            task = self._tasks.get(task_id)
            if not task or task.status == "cancelled":
                self._queue.task_done()
                continue

            task.status = "downloading"
            try:
                if task.future and not task.future.done():
                    task.future.set_result("start")
            except Exception:
                pass
            finally:
                self._queue.task_done()

queue_manager = QueueManager()
