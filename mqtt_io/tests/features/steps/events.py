import asyncio
import concurrent.futures
from typing import Any, Dict, Type

import yaml
from behave import given, then, when  # type: ignore
from behave.api.async_step import async_run_until_complete  # type: ignore
from mqtt_io import events
from mqtt_io.server import MqttIo

try:
    from unittest.mock import AsyncMock  # type: ignore[attr-defined]
except ImportError:
    from mock import AsyncMock  # type: ignore[attr-defined]

# pylint: disable=function-redefined,protected-access


@when("we subscribe to {event_type_name}")
def step(context: Any, event_type_name: str) -> None:
    mqttio: MqttIo = context.data["mqttio"]
    event_type = getattr(events, event_type_name)
    mock_sub = AsyncMock()
    context.data["event_subs"][event_type_name] = mock_sub
    mqttio.event_bus.subscribe(event_type, mock_sub)


@when("we fire a new {event_type_name} event with")  # type: ignore[no-redef]
@async_run_until_complete(loop="loop")
async def step(context: Any, event_type_name: str) -> None:
    data: Dict[str, Any] = yaml.safe_load(context.text)
    assert isinstance(data, dict), "Data provided to this step must be a YAML dict"
    mqttio: MqttIo = context.data["mqttio"]
    event_type: Type[events.Event] = getattr(events, event_type_name)
    event = event_type(**data)
    task_futures = mqttio.event_bus.fire(event)
    await asyncio.gather(*task_futures)


@when("we fire a new {event_type_name} event from another thread with")  # type: ignore[no-redef]
@async_run_until_complete(loop="loop")
async def step(context: Any, event_type_name: str) -> None:
    data: Dict[str, Any] = yaml.safe_load(context.text)
    assert isinstance(data, dict), "Data provided to this step must be a YAML dict"
    mqttio: MqttIo = context.data["mqttio"]
    event_type: Type[events.Event] = getattr(events, event_type_name)
    event = event_type(**data)

    with concurrent.futures.ThreadPoolExecutor() as executor:
        future = executor.submit(lambda: mqttio.event_bus.fire(event))
        task_futures = future.result()
    await asyncio.gather(*task_futures)


@then("{func_name} function should be subscribed to {event_type_name}")  # type: ignore[no-redef]
def step(context: Any, func_name: str, event_type_name: str) -> None:
    mqttio = context.data["mqttio"]
    event_type = getattr(events, event_type_name)
    assert func_name in {x.__name__ for x in mqttio.event_bus._listeners[event_type]}


@then("{event_type_name} is fired with")  # type: ignore[no-redef]
def step(context: Any, event_type_name: str) -> None:
    data = yaml.safe_load(context.text)
    assert isinstance(data, dict), "Data provided to this step must be a YAML dict"
    # event_type = getattr(events, event_type_name)
    mock_sub = context.data["event_subs"][event_type_name]
    event = mock_sub.call_args.args[0]
    for key, value in data.items():
        assert getattr(event, key) == value, f"Expecting event.{key} to be {value}"
