import types
import logging

_LOG = logging.getLogger(__name__)
_LOG.addHandler(logging.StreamHandler())
_LOG.setLevel(logging.DEBUG)


class Event:
    pass


class EventBus:
    def __init__(self, loop):
        self._loop = loop
        self._listeners = {}

    def fire(self, event):
        try:
            listeners = self._listeners[type(event)]
            _LOG.debug(
                "Found %s listener(s) for event type %r", len(listeners), type(event)
            )
        except KeyError:
            _LOG.debug("No listeners for event type %r", type(event))
            return

        for listener in listeners:
            self._loop.create_task(listener(event))

    def subscribe(self, event_type, callback):
        if not isinstance(event_type, type):
            raise TypeError(
                "event_type must be of type 'type'. Got type %r." % type(event_type)
            )
        if not isinstance(callback, types.FunctionType):
            raise TypeError(
                "callback must be of type 'types.FunctionType'. Got type %r."
                % type(callback)
            )
        if event_type in self._listeners:
            self._listeners[event_type].append(callback)
        else:
            self._listeners[event_type] = [callback]

        _LOG.debug(self._listeners)

        def remove_listener():
            self._listeners[event_type].remove(callback)

        return remove_listener
