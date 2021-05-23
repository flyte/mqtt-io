"""
Utils for MQTT IO project.
"""
import math
from typing import TYPE_CHECKING, Union

import trio
from trio_typing import TaskStatus


if TYPE_CHECKING:
    from typing import Any


async def hold_channel_open(
    channel: Union["trio.MemorySendChannel[Any]", "trio.MemoryReceiveChannel[Any]"],
    task_status: TaskStatus[None] = trio.TASK_STATUS_IGNORED,
) -> None:
    """
    Hold a channel open indefinitely. Useful for when you're sporadically cloning a
    channel but don't want to close the whole thing when you're finished with a clone.
    """
    async with channel:
        task_status.started()
        await trio.sleep(math.inf)
