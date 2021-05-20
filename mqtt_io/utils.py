"""
Utils for MQTT IO project.
"""
import asyncio
import math
from functools import wraps
from typing import Any, Coroutine, Optional, Union, cast

import trio

from mqtt_io.tasks import TransientTaskManager


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
    transient_tasks: TransientTaskManager,
    coro: Coroutine[Any, Any, None],
    task_future: Optional["asyncio.Future[asyncio.Task[Any]]"] = None,
) -> None:
    """
    Schedule a coroutine on the loop and add the Task to transient_tasks.
    """

    def callback() -> None:
        task = loop.create_task(coro)
        transient_tasks.add_task(task)
        if task_future is not None:
            task_future.set_result(task)

    loop.call_soon_threadsafe(callback)


async def hold_channel_open(
    channel: Union[trio.MemorySendChannel, trio.MemoryReceiveChannel],
    task_status: trio._core._run._TaskStatus = trio.TASK_STATUS_IGNORED,
):
    with channel:
        task_status.started()
        await trio.sleep(math.inf)


def set_result(results, key, func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        results[key] = await func(*args, **kwargs)

    return wrapper


class ResultNursery:
    def __init__(self):
        self.nursery_manager = trio.open_nursery()

    async def __aenter__(self):
        nursery = await self.nursery_manager.__aenter__()
        nursery.results = {}

        def start_soon_result(name, async_fn, *args):
            nursery.start_soon(
                set_result(nursery.results, name, async_fn), *args, name=name
            )

        nursery.start_soon_result = start_soon_result
        return nursery

    async def __aexit__(self, etype, exc, tb):
        await self.nursery_manager.__aexit__(etype, exc, tb)
