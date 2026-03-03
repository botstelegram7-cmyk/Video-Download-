import asyncio
from collections import defaultdict

_queues: dict = defaultdict(asyncio.Queue)
_semaphore = asyncio.Semaphore(5)


class QueueItem:
    def __init__(self, user_id: int, url: str, msg, extra: dict = None):
        self.user_id   = user_id
        self.url       = url
        self.msg       = msg
        self.extra     = extra or {}
        self.cancelled = False


async def enqueue(item: QueueItem) -> int:
    q = _queues[item.user_id]
    await q.put(item)
    return q.qsize()


async def cancel_user_queue(user_id: int) -> int:
    q = _queues[user_id]
    cancelled = 0
    while not q.empty():
        try:
            item = q.get_nowait()
            item.cancelled = True
            cancelled += 1
        except asyncio.QueueEmpty:
            break
    return cancelled


def get_queue_size(user_id: int) -> int:
    return _queues[user_id].qsize()


async def process_queue(user_id: int, processor):
    q = _queues[user_id]
    while not q.empty():
        item = await q.get()
        if item.cancelled:
            q.task_done()
            continue
        async with _semaphore:
            try:
                await processor(item)
            except Exception as e:
                print(f"[QUEUE] Error for {user_id}: {e}")
        q.task_done()
