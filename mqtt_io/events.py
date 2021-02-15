import asyncio
import logging
from abc import ABC
from dataclasses import dataclass
from types import FunctionType
from typing import Any, Awaitable, Callable, Dict, List, Optional, Type

_LOG = logging.getLogger(__name__)


@dataclass
class Event(ABC):
    pass


@dataclass
class DigitalInputChangedEvent(Event):
    input_name: str
    from_value: Optional[bool]
    to_value: bool


@dataclass
class DigitalOutputChangedEvent(Event):
    output_name: str
    to_value: bool


@dataclass
class SensorReadEvent(Event):
    sensor_name: str
    value: Any


class EventBus:
    def __init__(self, loop: asyncio.AbstractEventLoop):
        self._loop = loop
        self._listeners: Dict[Type[Event], List[Callable[[Any], Awaitable[None]]]] = {}

    def fire(self, event: Event) -> None:
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
            asyncio.run_coroutine_threadsafe(listener(event), self._loop)
            # self._loop.create_task(listener(event))

    def subscribe(
        self,
        event_class: Type[Event],
        callback: Callable[[Any], Awaitable[None]],
    ) -> Callable[[], None]:
        if not isinstance(event_class, type):
            raise TypeError(
                "event_class must be of type 'type'. Got type %s." % type(event_class)
            )
        if not isinstance(callback, FunctionType):
            raise TypeError(
                "callback must be of type 'FunctionType'. Got type %s." % type(callback)
            )
        if event_class in self._listeners:
            self._listeners[event_class].append(callback)
        else:
            self._listeners[event_class] = [callback]

        def remove_listener() -> None:
            self._listeners[event_class].remove(callback)

        return remove_listener
