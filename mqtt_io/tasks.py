"""
Utils for working with transient tasks.
"""
import asyncio
import logging
from asyncio import CancelledError
from typing import List, Optional, Any, cast  # pylint: disable=unused-import

_LOG = logging.getLogger(__name__)


class TransientTaskManager:
    """
    Manages a dynamic list of "transient" tasks.
    List is cleaned up in loop().
    new tasks can be added by add_task()
    """

    def __init__(self) -> None:
        self._ev: Optional[asyncio.Event] = None
        self._shut_down = False
        self.tasks: List["asyncio.Task[Any]"] = []

    @property
    def _event(self) -> "asyncio.Event":
        """
        Lazy initialized asyncio.Event()
        The event should be set, if a new task is added by add_task
        """
        if self._ev is None:
            self._ev = asyncio.Event()
        return self._ev

    async def loop(self) -> None:
        """
        await tasks added with add_task.
        Exceptions are caught and logged.
        If it gets cancelled, all child tasks are cancelled.
        MUST NOT be called multiple times.
        """
        tasks = self.tasks
        # "watch_task" to wake up when there is a new task
        watch_task = None
        event = self._event
        while self.tasks or not self._shut_down:
            event.clear()
            if not self._shut_down:
                if not watch_task:
                    watch_task = asyncio.get_event_loop().create_task(event.wait())
            try:
                done, _ = await asyncio.wait(
                    tasks + [cast("asyncio.Task[bool]", watch_task)],
                    return_when=asyncio.FIRST_COMPLETED,
                )
            except asyncio.CancelledError:
                # We got cancelled
                self._shut_down = True
                for task in tasks:
                    task.cancel()
                if watch_task:
                    watch_task.cancel()
                continue
            for ready_task in done:
                if ready_task is watch_task:
                    try:
                        await ready_task
                    except asyncio.CancelledError:
                        pass
                    watch_task = None
                    continue
                try:
                    await ready_task
                except asyncio.CancelledError:
                    pass
                except Exception:  # pylint: disable=broad-except
                    _LOG.exception("Exception in transient task %r", ready_task)
                tasks.remove(cast("asyncio.Task[Any]", ready_task))
        raise CancelledError()

    def add_task(self, task: "asyncio.Task[Any]") -> None:
        """
        Add a new task.
        Raises a RuntimeError if the loop was cancelled.
        """
        if self._shut_down:
            raise RuntimeError(
                "Tried to add a new task to a stopping TransientTaskManager!"
            )
        self.tasks.append(task)
        self._event.set()
