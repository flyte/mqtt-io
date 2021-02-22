from typing import Any

import yaml
from behave import given, then, when  # type: ignore
from mqtt_io.exceptions import ConfigValidationFailed
from mqtt_io.server import MqttIo

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
