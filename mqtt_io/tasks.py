import asyncio
import logging
from typing import List, Optional

_LOG = logging.getLogger(__name__)


class TransientTaskManager:
    def __init__(self):
        self._ev: "Optional[asyncio.Event]" = None
        self._shut_down = False
        self.tasks: "List[asyncio.Task]" = []

    @property
    def _event(self) -> "asyncio.Event":
        if self._ev is None:
            self._ev = asyncio.Event()
        return self._ev

    async def loop(self):
        tasks = self.tasks
        # "watch_task" to wake up when there is a new task
        watch_task = None
        event = self._event
        while True:
            event.clear()
            if not self._shut_down:
                if not watch_task:
                    watch_task = asyncio.create_task(event.wait())
            try:
                done, pending = await asyncio.wait(tasks + [watch_task], return_when=asyncio.FIRST_COMPLETED)
            except asyncio.CancelledError:
                # We got cancelled
                self._shut_down = True
                for t in tasks:
                    t.cancel()
                continue
            if watch_task in done:
                watch_task = None
            for task in done:
                if task is watch_task:
                    continue
                try:
                    await task
                except asyncio.CancelledError:
                    pass
                except Exception:  # pylint: disable=broad-except
                    _LOG.exception("Exception in transient task %r", task)
                tasks.remove(task)

    def add_task(self, task_or_coro):
        if self._shut_down:
            raise RuntimeError('Tried to add a new task to a stopping TransientTaskManager!')
        if not asyncio.isfuture(task_or_coro):
            task_or_coro = asyncio.create_task(task_or_coro)
        self.tasks.append(task_or_coro)
