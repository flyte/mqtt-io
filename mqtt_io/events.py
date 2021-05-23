"""
Event framework for subscribing to and firing events.
"""
import logging
import math
from abc import ABC
from dataclasses import dataclass
from typing import Any, Callable, Coroutine, Optional, Type

import trio
from trio_typing import TaskStatus

from mqtt_io.types import EventT

from .utils import hold_channel_open

_LOG = logging.getLogger(__name__)

# Unfortunately can't use Callable[[Event], Coroutine[Any, Any, None]] here because
# Callable[] is 'contravariant'.
ListenerType = Callable[[Any], Coroutine[Any, Any, None]]


@dataclass
class Event(ABC):
    """
    Base Event class.
    """


@dataclass
class DigitalInputChangedEvent(Event):
    """
    A digital input changed state.
    """

    input_name: str
    from_value: Optional[bool]
    to_value: bool


@dataclass
class DigitalOutputChangedEvent(Event):
    """
    A digital output changed state.
    """

    output_name: str
    to_value: bool


@dataclass
class SensorReadEvent(Event):
    """
    A value was read from a sensor.
    """

    sensor_name: str
    value: Any


@dataclass
class StreamDataReadEvent(Event):
    """
    Some data was read from a stream.
    """

    stream_name: str
    data: bytes


@dataclass
class StreamDataSentEvent(Event):
    """
    Some data was written to a stream.
    """

    stream_name: str
    data: bytes


# class EventBusChannels(
#     Dict[
#         Type[Event],
#         List[Tuple[trio.MemorySendChannel[Event], trio.MemoryReceiveChannel[Event]]],
#     ]
# ):
#     def __setitem__(
#         self,
#         key: Type[EventT],
#         item: List[
#             Tuple[trio.MemorySendChannel[EventT], trio.MemoryReceiveChannel[EventT]]
#         ],
#     ) -> None:
#         super().__setitem__(key, item)

#     def __getitem__(
#         self, key: Type[EventT]
#     ) -> List[Tuple[trio.MemorySendChannel[EventT], trio.MemoryReceiveChannel[EventT]]]:
#         pass


class EventBus:
    """
    Provides subscriptions to individual events using channels.
    """

    def __init__(self) -> None:
        self._nursery: Optional[trio.Nursery] = None
        self._channels = {}

        # self._channels: Dict[
        #     Type[Event],
        #     List[Tuple[trio.MemorySendChannel[Event], trio.MemoryReceiveChannel[Event]]],
        # ] = EventBusChannels()

        # self._channels: Dict[
        #     Type[EventT],
        #     List[
        #         Tuple[trio.MemorySendChannel[EventT], trio.MemoryReceiveChannel[EventT]]
        #     ],
        # ] = {}

    async def run(
        self,
        task_status: TaskStatus[None] = trio.TASK_STATUS_IGNORED,
    ) -> None:
        """
        Run the event bus.
        """
        async with trio.open_nursery() as nursery:
            self._nursery = nursery
            nursery.start_soon(lambda: trio.sleep(math.inf))
            task_status.started()

    def close(self) -> None:
        """
        Close the event bus.
        """
        if self._nursery is None:
            return
        self._nursery.cancel_scope.cancel()
        self._nursery = None

    async def subscribe(
        self, event_class: Type[EventT], buffer_size: int = 0
    ) -> "trio.MemoryReceiveChannel[EventT]":
        """
        Subscribe to an event and receive a trio.MemoryReceiveChannel on which you will
        receive events of the requested type as they occur.
        """
        if self._nursery is None:
            raise trio.BrokenResourceError("The event bus is not running")
        tx_chan: "trio.MemorySendChannel[EventT]"
        rx_chan: "trio.MemoryReceiveChannel[EventT]"
        tx_chan, rx_chan = trio.open_memory_channel(max_buffer_size=buffer_size)
        self._channels.setdefault(event_class, []).append((tx_chan, rx_chan))

        await self._nursery.start(hold_channel_open, tx_chan)
        return rx_chan

    def fire(self, event: EventT) -> None:
        """
        Fire an event.
        """
        if self._nursery is None:
            raise trio.BrokenResourceError("The event bus is not running")

        async def send_event(tx_chan: "trio.MemorySendChannel[EventT]") -> None:
            async with tx_chan:
                try:
                    tx_chan.send_nowait(event)
                except trio.WouldBlock:
                    pass

        for tx_chan, _ in self._channels.get(type(event), []):
            self._nursery.start_soon(send_event, tx_chan.clone())
