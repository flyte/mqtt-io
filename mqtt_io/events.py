import types
import logging

_LOG = logging.getLogger(__name__)


class Event:
    pass


class EventBus:
    def __init__(self, loop):
        self._loop = loop
        self._listeners = {}

    def fire(self, event):
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
            self._loop.create_task(listener(event))

    def subscribe(self, event_class, callback):
        if not isinstance(event_class, type):
            raise TypeError(
                "event_class must be of type 'type'. Got type %s." % type(event_class)
            )
        if not isinstance(callback, types.FunctionType):
            raise TypeError(
                "callback must be of type 'types.FunctionType'. Got type %s."
                % type(callback)
            )
        if event_class in self._listeners:
            self._listeners[event_class].append(callback)
        else:
            self._listeners[event_class] = [callback]

        def remove_listener():
            self._listeners[event_class].remove(callback)

        return remove_listener
