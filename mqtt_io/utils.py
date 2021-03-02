"""
Utils for MQTT IO project.
"""
import asyncio
from typing import Any, Coroutine, List, Optional, cast


class PriorityCoro:
    """
    An object for adding a coroutine to an asyncio.PriorityQueue.
    """

    def __init__(self, coro: Coroutine[Any, Any, Any], priority: int):
        self.coro = coro
        self.priority = priority

    def __lt__(self, other: Any) -> bool:
        return cast(bool, self.priority < other.priority)

    def __eq__(self, other: Any) -> bool:
        return cast(bool, self.priority == other.priority)


def create_unawaited_task_threadsafe(
    loop: asyncio.AbstractEventLoop,
    transient_tasks: List["asyncio.Task[Any]"],
    coro: Coroutine[Any, Any, None],
    task_future: Optional["asyncio.Future[asyncio.Task[Any]]"] = None,
) -> None:
    """
    Schedule a coroutine on the loop and add the Task to transient_tasks.
    """

    def callback() -> None:
        task = loop.create_task(coro)
        transient_tasks.append(task)
        if task_future is not None:
            task_future.set_result(task)

    loop.call_soon_threadsafe(callback)
