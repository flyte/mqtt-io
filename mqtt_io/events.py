"""
Event framework for subscribing to and firing events with asyncio callbacks.
"""

import asyncio
import logging
from abc import ABC
from dataclasses import dataclass
from typing import Any, Awaitable, Callable, Dict, List, Optional, Type

from .types import UnawaitedTaskType

_LOG = logging.getLogger(__name__)


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


class EventBus:
    """
    Event bus that handles subscribing to specific events and firing coroutine callbacks.
    """

    def __init__(
        self,
        loop: asyncio.AbstractEventLoop,
        unawaited_tasks: List[UnawaitedTaskType],
    ):
        self._loop = loop
        self._unawaited_tasks = unawaited_tasks
        self._listeners: Dict[Type[Event], List[Callable[[Any], Awaitable[None]]]] = {}

    def fire(self, event: Event) -> None:
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
            return

        for listener in listeners:
            # Run threadsafe in case we're firing events from interrupt callback threads
            self._unawaited_tasks.append(
                asyncio.run_coroutine_threadsafe(listener(event), self._loop)
            )

    def subscribe(
        self,
        event_class: Type[Event],
        # Unfortunately can't use Callable[[Event], Awaitable[None]] here because
        # Callable[] is 'contravariant'.
        callback: Callable[[Any], Awaitable[None]],
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
