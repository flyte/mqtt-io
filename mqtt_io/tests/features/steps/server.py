import asyncio
from inspect import iscoroutinefunction
from typing import Any, Union
from unittest.mock import Mock

import yaml
from behave import given, then, when  # type: ignore
from behave.api.async_step import async_run_until_complete  # type: ignore
from mqtt_io.exceptions import ConfigValidationFailed
from mqtt_io.mqtt import MQTTMessage, MQTTMessageSend
from mqtt_io.server import MqttIo

try:
    from unittest.mock import AsyncMock  # type: ignore[attr-defined]
except ImportError:
    from mock import AsyncMock  # type: ignore[attr-defined]

# pylint: disable=function-redefined


@when("we instantiate MqttIo")  # type: ignore[no-redef]
def step(context: Any) -> None:
    context.data["mqttio"] = MqttIo(context.data["config"], loop=context.data["loop"])


@when("we initialise {target}")  # type: ignore[no-redef]
def step(context: Any, target: str) -> None:
    target = target.lower().replace(" ", "_")
    try:
        getattr(context.data["mqttio"], f"_init_{target}")()
    except ConfigValidationFailed as exc:
        context.data["validation_error"] = exc


@when("we mock {method_name} on MqttIo")  # type: ignore[no-redef]
def step(context: Any, method_name: str) -> None:
    mqttio: MqttIo = context.data["mqttio"]
    mock = AsyncMock() if iscoroutinefunction(getattr(mqttio, method_name)) else Mock()
    context.data["mocks"][f"mqttio.{method_name}"] = mock
    setattr(mqttio, method_name, mock)


@when("we {lock_unlock} interrupt lock for {pin_name}")  # type: ignore[no-redef]
def step(context: Any, lock_unlock: str, pin_name: str) -> None:
    assert lock_unlock in ("lock", "unlock")
    mqttio: MqttIo = context.data["mqttio"]
    lock = mqttio.interrupt_locks[pin_name]
    locked = lock.locked()
    if lock_unlock == "lock":
        assert not locked, "Can't lock an already locked lock"
        assert lock.acquire(blocking=False)
    else:
        assert locked, "Can't unlock an already unlocked lock"
        lock.release()


@when("we run async tasks")  # type: ignore[no-redef]
@async_run_until_complete(loop="loop")
async def step(context: Any):
    pass


@then("interrupt lock for {pin_name} should be {locked_unlocked}")  # type: ignore[no-redef]
def step(context: Any, locked_unlocked: str, pin_name: str) -> None:
    assert locked_unlocked in ("locked", "unlocked")
    mqttio: MqttIo = context.data["mqttio"]
    lock = mqttio.interrupt_locks[pin_name]
    locked = lock.locked()
    assert locked if locked_unlocked == "locked" else not locked


@then("{method_name} on MqttIo should be called with")  # type: ignore[no-redef]
def step(context: Any, method_name: str):
    mock: Union[Mock, AsyncMock] = context.data["mocks"][f"mqttio.{method_name}"]
    data = yaml.safe_load(context.text)
    call_args, call_kwargs = mock.call_args
    for arg_index, arg_value in data.get("args", {}).items():
        assert (
            call_args[arg_index] == arg_value
        ), f"Should have been called with {arg_value} at args index {arg_index}"
    for kwarg_key, kwarg_value in data.get("kwargs", {}).items():
        assert (
            call_kwargs[kwarg_key] == kwarg_value
        ), f"Should have been called with {kwarg_value} at kwargs key {kwarg_key}"


@then("_mqtt_publish on MqttIo should be called with MQTT message")  # type: ignore[no-redef]
def step(context: Any):
    mock: Union[Mock, AsyncMock] = context.data["mocks"]["mqttio._mqtt_publish"]
    data = yaml.safe_load(context.text)
    assert mock.called, "_mqtt_publish should have been called"
    msg: MQTTMessageSend = mock.call_args.args[0]
    assert isinstance(msg, MQTTMessageSend), "Should have been called with an MQTTMessage"
    if "topic" in data:
        assert msg.topic == data["topic"]
    if "payload" in data:
        try:
            payload_str = msg.payload.decode("utf8")
        except UnicodeDecodeError as err:
            raise AssertionError(
                "Payload was specified but a non-unicode one was published"
            ) from err
        assert (
            payload_str == data["payload"]
        ), f"Payload was '{payload_str}' but we were expecting '{data['payload']}'"


@then("{method_name} on MqttIo {should_shouldnt} be called")  # type: ignore[no-redef]
def step(context: Any, method_name: str, should_shouldnt: str):
    assert should_shouldnt in ("should", "shouldn't")
    mock: Union[Mock, AsyncMock] = context.data["mocks"][f"mqttio.{method_name}"]
    if should_shouldnt == "should":
        mock.assert_called()
    else:
        mock.assert_not_called()


@then("{module} module {name} should be initialised")  # type: ignore[no-redef]
def step(context: Any, module: str, name: str) -> None:
    mqttio = context.data["mqttio"]
    assert name in getattr(mqttio, f"{module.lower()}_modules")


@then("{module} module {name} should have {count:d} call(s) to {attribute}")  # type: ignore[no-redef]
def step(context: Any, module: str, name: str, count: int, attribute: str) -> None:
    mqttio = context.data["mqttio"]
    module = getattr(mqttio, f"{module.lower()}_modules")[name]
    assert getattr(module, attribute).call_count == count


@then("{target} config {name} should exist")  # type: ignore[no-redef]
def step(context: Any, target: str, name: str) -> None:
    mqttio = context.data["mqttio"]
    assert getattr(mqttio, f"{target.lower().replace(' ', '_')}_configs")[name]


@then("{target} config {name} should contain")  # type: ignore[no-redef]
def step(context: Any, target: str, name: str) -> None:
    data = yaml.safe_load(context.text)
    assert isinstance(
        data, dict
    ), "Data passed to this step should be a YAML formatted dict"
    mqttio = context.data["mqttio"]
    target_config = getattr(mqttio, f"{target.lower().replace(' ', '_')}_configs")[name]
    for key, value in data.items():
        assert target_config[key] == value


@then("GPIO module {module_name} {should_shouldnt} have an output queue initialised")  # type: ignore[no-redef]
def step(context: Any, module_name: str, should_shouldnt: str) -> None:
    assert should_shouldnt in ("should", "shouldn't")
    mqttio = context.data["mqttio"]
    test = all(
        (
            "mock" in mqttio.gpio_output_queues,
            isinstance(mqttio.gpio_output_queues.get("mock"), asyncio.Queue),
        )
    )

    assert test if should_shouldnt == "should" else not test
