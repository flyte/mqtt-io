from typing import Any
import yaml
from behave import given, then, when  # type: ignore
from mqtt_io.config import validate_and_normalise_main_config
from mqtt_io.exceptions import ConfigValidationFailed
from mqtt_io.types import ConfigType

# pylint: disable=function-redefined


@given("the config has an mqtt section")
def step(context: Any) -> None:
    config = context.data["raw_config"]
    config["mqtt"] = {}


@given("a valid config")  # type: ignore[no-redef]
def step(context: Any) -> None:
    config = context.data["raw_config"]
    config["mqtt"] = dict(host="localhost")


@given("the config has an entry in {section} with")  # type: ignore[no-redef]
def step(context: Any, section: str) -> None:
    data = yaml.safe_load(context.text)
    config = context.data["raw_config"]
    config.setdefault(section, []).append(data)


@given("the {section} config section dict contains")  # type: ignore[no-redef]
def step(context: Any, section: str) -> None:
    data = yaml.safe_load(context.text)
    config = context.data["raw_config"]
    config.setdefault(section, {}).update(data)


@when("we validate the main config")  # type: ignore[no-redef]
def step(context):
    try:
        context.data["config"] = validate_and_normalise_main_config(
            context.data["raw_config"]
        )
    except ConfigValidationFailed as exc:
        context.data["validation_error"] = exc


@then("config validation fails")  # type: ignore[no-redef]
def step(context):
    print("--- Config file ---")
    print(yaml.dump(context.data["raw_config"]))
    assert "validation_error" in context.data, "Config validation should have failed"


@then("the config validates")  # type: ignore[no-redef]
def step(context):
    print("--- Config file ---")
    print(yaml.dump(context.data["raw_config"]))
    try:
        print("--- Validation Errors ---")
        print(context.data["validation_error"])
    except KeyError:
        pass
    assert "validation_error" not in context.data, "Config should validate"
    assert (
        "config" in context.data
    ), 'Validated config should be in context.data["config"] (test error)'
