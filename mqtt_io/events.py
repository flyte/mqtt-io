"""
Event framework for subscribing to and firing events.
"""
import logging
import math
from abc import ABC
from dataclasses import dataclass
from mqtt_io.types import TaskStatus
from typing import Any, Callable, Coroutine, Dict, List, Optional, Tuple, Type

import trio

from .tasks import TransientTaskManager
from .utils import create_unawaited_task_threadsafe, hold_channel_open

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


# class EventBus:
#     """
#     Event bus that handles subscribing to specific events and firing coroutine callbacks.
#     """

#     def __init__(self, nursery: trio.Nursery):
#         self._nursery = nursery
#         self._listeners: Dict[Type[Event], List[ListenerType]] = {}

#     def fire(self, event: Event) -> None:
#         """
#         Add callback functions that have subscribed to this event type to the nursery.
#         """
#         event_class = type(event)
#         try:
#             listeners = self._listeners[event_class]
#             _LOG.debug(
#                 "Found %s listener(s) for event type %s",
#                 len(listeners),
#                 event_class.__name__,
#             )
#         except KeyError:
#             _LOG.debug("No listeners for event type %s", event_class.__name__)
#             return

#         for listener in listeners:
#             self._nursery.start_soon(listener, event)

#     def subscribe(
#         self,
#         event_class: Type[Event],
#         callback: ListenerType,
#     ) -> Callable[[], None]:
#         """
#         Add a coroutine to be used as a callback when the given event class is fired.
#         """
#         if not isinstance(event_class, type):
#             raise TypeError(
#                 "event_class must be of type 'type'. Got type %s." % type(event_class)
#             )
#         if not Event in event_class.mro():
#             raise TypeError("Event class must be a subclass of mqtt_io.events.Event")
#         if not callable(callback):
#             raise TypeError("callback must be callable. Got type %s." % type(callback))

#         self._listeners.setdefault(event_class, []).append(callback)

#         def remove_listener() -> None:
#             self._listeners[event_class].remove(callback)

#         return remove_listener


class EventBus:
    def __init__(self) -> None:
        self._nursery: Optional[trio.Nursery] = None
        self._channels: Dict[
            Type[Event], List[Tuple[trio.MemorySendChannel, trio.MemoryReceiveChannel]]
        ] = {}

    async def run(self, task_status: TaskStatus = trio.TASK_STATUS_IGNORED) -> None:
        async with trio.open_nursery() as nursery:
            self._nursery = nursery
            nursery.start_soon(lambda: trio.sleep(math.inf))
            task_status.started()

    def close(self) -> None:
        if self._nursery is None:
            return
        self._nursery.cancel_scope.cancel()
        self._nursery = None

    async def subscribe(
        self, event_class: Type[Event], buffer_size: int = 0
    ) -> trio.MemoryReceiveChannel:
        if self._nursery is None:
            raise trio.BrokenResourceError("The event bus is not running")

        tx_chan, rx_chan = trio.open_memory_channel(max_buffer_size=buffer_size)
        self._channels.setdefault(event_class, []).append((tx_chan, rx_chan))

        await self._nursery.start(hold_channel_open, tx_chan)
        return rx_chan

    def fire(self, event: Event) -> None:
        if self._nursery is None:
            raise trio.BrokenResourceError("The event bus is not running")

        async def send_event(tx_chan: trio.MemorySendChannel) -> None:
            async with tx_chan:
                try:
                    tx_chan.send_nowait(event)
                except trio.WouldBlock:
                    pass

        for tx_chan, _ in self._channels.get(type(event), []):
            self._nursery.start_soon(send_event, tx_chan.clone())
