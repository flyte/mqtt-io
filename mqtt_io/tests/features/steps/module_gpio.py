import asyncio
from typing import Any

from behave import given, then, when  # type: ignore
from behave.api.async_step import async_run_until_complete  # type: ignore
from mqtt_io.modules.gpio import InterruptEdge, PinDirection
from mqtt_io.server import MqttIo

# pylint: disable=function-redefined,protected-access


# TODO: Tasks pending completion -@flyte at 22/02/2021, 16:56:52
# Add a test to go through all of the modules in the gpio dir and test them for compliance


def get_coro(task: "asyncio.Task[Any]") -> Any:
    """
    Get a task's coroutine.
    """
    # pylint: disable=protected-access
    if hasattr(task, "get_coro"):
        return task.get_coro()  # type: ignore[attr-defined]
    if hasattr(task, "_coro"):
        return task._coro  # type: ignore[attr-defined]
    raise AttributeError("Unable to get task's coro")


@then("GPIO module {module_name} should have a pin config for {pin_name}")
def step(context: Any, module_name: str, pin_name: str) -> None:
    mqttio = context.data["mqttio"]
    module = mqttio.gpio_modules[module_name]
    assert pin_name in {x["name"] for x in module.pin_configs.values()}


@then("GPIO module {module_name} should have a setup_pin() call for {pin_name}")  # type: ignore[no-redef]
def step(context: Any, module_name: str, pin_name: str) -> None:
    mqttio = context.data["mqttio"]
    module = mqttio.gpio_modules[module_name]
    call_pin_names = {
        kwargs["pin_config"]["name"] for _, kwargs in module.setup_pin.call_args_list
    }
    assert pin_name in call_pin_names


@then("{pin_name} pin should have been set up as an {io_dir}")  # type: ignore[no-redef]
def step(context: Any, pin_name: str, io_dir: str) -> None:
    assert io_dir in ("input", "output")
    mqttio = context.data["mqttio"]
    io_conf = getattr(mqttio, f"digital_{io_dir}_configs")[pin_name]
    module = mqttio.gpio_modules[io_conf["module"]]
    pin_dirs = {
        kwargs["pin_config"]["name"]: args[1]
        for args, kwargs in module.setup_pin.call_args_list
    }
    if io_dir == "input":
        assert pin_dirs[pin_name] == PinDirection.INPUT
    else:
        assert pin_dirs[pin_name] == PinDirection.OUTPUT


@then("GPIO module {module_name} {should_shouldnt} have a {setup_func_name}() call for {pin_name}")  # type: ignore[no-redef]
def step(
    context: Any,
    module_name: str,
    should_shouldnt: str,
    setup_func_name: str,
    pin_name: str,
) -> None:
    assert should_shouldnt in ("should", "shouldn't")
    mqttio = context.data["mqttio"]
    module = mqttio.gpio_modules[module_name]
    relevant_call_args = None
    for call_args, _ in getattr(module, setup_func_name).call_args_list:  # type: ignore[attr-defined]
        if call_args[2]["name"] == pin_name:
            relevant_call_args = call_args

    if should_shouldnt == "should":
        assert relevant_call_args is not None
    else:
        assert relevant_call_args is None


@then("a digital input poller task {is_isnt} added for {pin_name}")  # type: ignore[no-redef]
def step(context: Any, is_isnt: str, pin_name: str):
    assert is_isnt in ("is", "isn't")
    mqttio = context.data["mqttio"]

    poller_task_pin_names = {
        get_coro(task).cr_frame.f_locals["in_conf"]["name"]
        for task in mqttio.transient_tasks
        if isinstance(task, asyncio.Task)  # concurrent.Future doesn't have get_coro()
        and get_coro(task).__name__ == "digital_input_poller"
    }
    if is_isnt == "is":
        assert (
            pin_name in poller_task_pin_names
        ), "Should have a digital input poller task added to transient_tasks"
    else:
        assert (
            pin_name not in poller_task_pin_names
        ), "Shouldn't have a digital input poller task added to transient_tasks"

    poller_task_pin_names = {
        get_coro(task).cr_frame.f_locals["in_conf"]["name"]
        for task in asyncio.Task.all_tasks(loop=mqttio.loop)
        if get_coro(task).__name__ == "digital_input_poller"
    }
    if is_isnt == "is":
        assert (
            pin_name in poller_task_pin_names
        ), "Should have a digital input poller task added to the event loop"
    else:
        assert (
            pin_name not in poller_task_pin_names
        ), "Shouldn't have a digital input poller task added to the event loop"


@then("a digital output loop task {is_isnt} added for GPIO module {module_name}")  # type: ignore[no-redef]
def step(context: Any, is_isnt: str, module_name: str):
    assert is_isnt in ("is", "isn't")
    mqttio = context.data["mqttio"]
    module = mqttio.gpio_modules[module_name]
    task_modules = {
        get_coro(task).cr_frame.f_locals["module"]
        for task in mqttio.transient_tasks
        if isinstance(task, asyncio.Task)  # concurrent.Future doesn't have get_coro()
        and get_coro(task).__name__ == "digital_output_loop"
    }
    if is_isnt == "is":
        assert (
            module in task_modules
        ), "Should have a digital output loop task added to transient_tasks"
    else:
        assert (
            module not in task_modules
        ), "Shouldn't have a digital output loop task added to transient_tasks"

    task_modules = {
        get_coro(task).cr_frame.f_locals["module"]
        for task in asyncio.Task.all_tasks(loop=mqttio.loop)
        if get_coro(task).__name__ == "digital_output_loop"
    }
    if is_isnt == "is":
        assert (
            module in task_modules
        ), "Should have a digital output loop task added to the event loop"
    else:
        assert (
            module not in task_modules
        ), "Shouldn't have a digital output loop task added to the event loop"


@then("{pin_name} {should_shouldnt} be configured as a remote interrupt")  # type: ignore[no-redef]
def step(context: Any, pin_name: str, should_shouldnt: str):
    assert should_shouldnt in ("should", "shouldn't")
    mqttio = context.data["mqttio"]
    in_conf = mqttio.digital_input_configs[pin_name]
    module = mqttio.gpio_modules[in_conf["module"]]
    is_remote_interrupt = module.remote_interrupt_for(in_conf["pin"])
    if should_shouldnt == "should":
        assert is_remote_interrupt
    else:
        assert not is_remote_interrupt


@then("{pin_name} should be configured as a {direction_str} interrupt")  # type: ignore[no-redef]
def step(context: Any, pin_name: str, direction_str: str):
    mqttio = context.data["mqttio"]
    in_conf = mqttio.digital_input_configs[pin_name]
    module = mqttio.gpio_modules[in_conf["module"]]
    direction = module.interrupt_edges[in_conf["pin"]]
    assert direction == getattr(InterruptEdge, direction_str.upper())


@when("{pin_name} reads a value of {value_str} with a last value of {last_value_str}")  # type: ignore[no-redef]
@async_run_until_complete(loop="loop")
async def step(context: Any, pin_name: str, value_str: str, last_value_str: str) -> None:
    assert value_str in ("true", "false")
    assert last_value_str in ("null", "true", "false")
    value_map = dict(true=True, false=False, null=None)
    mqttio: MqttIo = context.data["mqttio"]
    in_conf = mqttio.digital_input_configs[pin_name]
    value = value_map[value_str]
    last_value = value_map[last_value_str]
    await mqttio._handle_digital_input_value(in_conf, value, last_value)


@when("we set digital output {pin_name} to {on_off}")  # type: ignore[no-redef]
@async_run_until_complete(loop="loop")
async def step(context: Any, pin_name: str, on_off: str) -> None:
    assert on_off in ("on", "off")
    mqttio: MqttIo = context.data["mqttio"]
    out_conf = mqttio.digital_output_configs[pin_name]
    module = mqttio.gpio_modules[out_conf["module"]]
    await mqttio.set_digital_output(module, out_conf, on_off == "on")
