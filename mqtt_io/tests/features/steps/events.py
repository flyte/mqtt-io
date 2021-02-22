from typing import Any

from behave import given, then, when  # type: ignore
from mqtt_io import events

# pylint: disable=function-redefined,protected-access


@then("{func_name} function should be subscribed to {event_type_name}")  # type: ignore
def step(context: Any, func_name: str, event_type_name: str) -> None:
    mqttio = context.data["mqttio"]
    event_type = getattr(events, event_type_name)
    assert func_name in {x.__name__ for x in mqttio.event_bus._listeners[event_type]}
