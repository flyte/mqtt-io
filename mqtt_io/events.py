"""
Event framework for subscribing to and firing events with asyncio callbacks.
"""

import asyncio
import logging
from abc import ABC
from dataclasses import dataclass
from typing import Any, Callable, Coroutine, Dict, List, Optional, Type

from .utils import create_unawaited_task_threadsafe

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

@dataclass
class StreamDataSubscribeEvent(Event):
    """
    Trigger MQTT subscribe
    """

@dataclass
class DigitalSubscribeEvent(Event):
    """
    Trigger MQTT subscribe
    """


class EventBus:
    """
    Event bus that handles subscribing to specific events and firing coroutine callbacks.
    """

    def __init__(
        self,
        loop: asyncio.AbstractEventLoop,
        transient_tasks: List["asyncio.Task[Any]"],
    ):
        self._loop = loop
        self._transient_tasks = transient_tasks
        self._listeners: Dict[Type[Event], List[ListenerType]] = {}

    def fire(self, event: Event) -> List["asyncio.Future[asyncio.Task[Any]]"]:
        """
        Add callback functions that have subscribed to this event type to the task loop.
        """
        event_class = type(event)
        try:
            listeners = self._listeners[event_class]
            _LOG.debug(
                "Found %s listener(s) for event type %s",
                len(listeners),
                event_class.__name__,
            )
        except KeyError:
            _LOG.debug("No listeners for event type %s", event_class.__name__)
            return []

        task_futures: "List[asyncio.Future[asyncio.Task[Any]]]" = []
        for listener in listeners:
            # Pass in a future on which the asyncio.Task will be set when the coro
            # has been scheduled on the loop.
            fut: "asyncio.Future[asyncio.Task[Any]]" = self._loop.create_future()
            task_futures.append(fut)
            # Run threadsafe in case we're firing events from interrupt callback threads
            create_unawaited_task_threadsafe(
                self._loop, self._transient_tasks, listener(event), fut
            )
        return task_futures

    def subscribe(
        self,
        event_class: Type[Event],
        callback: ListenerType,
    ) -> Callable[[], None]:
        """
        Add a coroutine to be used as a callback when the given event class is fired.
        """
        if not isinstance(event_class, type):
            raise TypeError(
                "event_class must be of type 'type'. Got type %s." % type(event_class)
            )
        if not Event in event_class.mro():
            raise TypeError("Event class must be a subclass of mqtt_io.events.Event")
        if not callable(callback):
            raise TypeError("callback must be callable. Got type %s." % type(callback))
        self._listeners.setdefault(event_class, []).append(callback)

        def remove_listener() -> None:
            self._listeners[event_class].remove(callback)

        return remove_listener
