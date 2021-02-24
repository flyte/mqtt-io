"""
Utils for MQTT IO project.
"""
import asyncio
from typing import Any, Coroutine, List, cast


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
) -> None:
    """
    Schedule a coroutine on the loop and add the Task to transient_tasks.
    """

    def callback() -> None:
        transient_tasks.append(loop.create_task(coro))

    loop.call_soon_threadsafe(callback)
