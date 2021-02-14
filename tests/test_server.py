import asyncio
import warnings

import pytest
import yaml
from mqtt_io.config import get_main_schema, validate_and_normalise_config
from mqtt_io.events import DigitalInputChangedEvent, DigitalOutputChangedEvent
from mqtt_io.modules.gpio import InterruptEdge, PinDirection

warnings.filterwarnings("ignore", category=DeprecationWarning)
from mqtt_io.server import MqttIo

# pylint: disable=redefined-outer-name, protected-access


def prepare_config(yaml_config: str) -> dict:
    schema = get_main_schema()
    config = yaml.safe_load(yaml_config)
    return validate_and_normalise_config(config, schema)


@pytest.fixture
def mqttio_minimal() -> MqttIo:
    config = prepare_config(
        """
mqtt:
    host: localhost
"""
    )
    return MqttIo(config)


@pytest.fixture
def mqttio_mock_gpio_module() -> MqttIo:
    config = prepare_config(
        """
mqtt:
    host: localhost

gpio_modules:
    - name: mock
      module: test.mock
      test: yes
"""
    )
    return MqttIo(config)


@pytest.fixture
def mqttio_mock_sensor_module() -> MqttIo:
    config = prepare_config(
        """
mqtt:
    host: localhost

sensor_modules:
    - name: mock
      module: test.mock
      test: yes
"""
    )
    return MqttIo(config)


@pytest.fixture
def mqttio_mock_digital_inputs() -> MqttIo:
    """
    Configure the software with one polled input, one interrupt and one interrupt
    configured as a remote interrupt for another pin.
    """
    config = prepare_config(
        """
mqtt:
    host: localhost

gpio_modules:
    - name: mock
      module: test.mock

digital_inputs:
    - name: mock0
      module: mock
      pin: 0

    - name: mock1
      module: mock
      pin: 1
      interrupt: rising

    - name: mock2
      module: mock
      pin: 2
      interrupt: falling
      interrupt_for:
          - mock0
"""
    )
    return MqttIo(config)


@pytest.fixture
def mqttio_mock_digital_outputs() -> MqttIo:
    """"""
    config = prepare_config(
        """
mqtt:
    host: localhost

gpio_modules:
    - name: mock
      module: test.mock

digital_outputs:
    - name: mock0
      module: mock
      pin: 0
"""
    )
    return MqttIo(config)


def test_init_gpio_modules(mqttio_mock_gpio_module: MqttIo):
    mqttio = mqttio_mock_gpio_module
    assert not mqttio.gpio_modules, "Nothing should be initialised yet"

    mqttio._init_gpio_modules()
    assert (
        "mock" in mqttio.gpio_modules
    ), "Mock module called 'mock' should be initialised"

    mock_module = mqttio.gpio_modules["mock"]
    assert (
        mock_module.setup_module.call_count == 1
    ), "Should only be one call to setup_module()"

    assert mock_module.config[
        "test"
    ], "Module config should have been validated and initialised"


def test_init_sensor_modules(mqttio_mock_sensor_module: MqttIo):
    mqttio = mqttio_mock_sensor_module
    assert not mqttio.sensor_modules, "Nothing should be initialised yet"

    mqttio._init_sensor_modules()
    assert (
        "mock" in mqttio.sensor_modules
    ), "Mock module called 'mock' should be initialised"

    mock_module = mqttio.sensor_modules["mock"]
    assert (
        mock_module.setup_sensor.call_count == 1
    ), "Should only be one call to setup_sensor()"

    assert mock_module.config[
        "test"
    ], "Module config should have been validated and initialised"


def test_init_digital_inputs_event_sub(mqttio_mock_digital_inputs: MqttIo):
    mqttio = mqttio_mock_digital_inputs
    assert not mqttio.digital_input_configs, "Nothing should be initialised yet"

    mqttio._init_gpio_modules()
    mqttio._init_digital_inputs()

    assert DigitalInputChangedEvent in mqttio.event_bus._listeners
    assert mqttio.event_bus._listeners[
        DigitalInputChangedEvent
    ], "Should be an event subscription for DigitalInputChangedEvent"
    assert "publish_callback" in [
        x.__name__ for x in mqttio.event_bus._listeners[DigitalInputChangedEvent]
    ], "publish_callback() should be subscribed to DigitalInputChangedEvent"


def test_init_digital_inputs_no_int(mqttio_mock_digital_inputs: MqttIo):
    """
    Check the initialisation process done for a polled digital input.
    """
    pin = 0
    mqttio = mqttio_mock_digital_inputs
    mqttio._init_gpio_modules()
    mqttio._init_digital_inputs()
    assert (
        "mock0" in mqttio.digital_input_configs
    ), "The config for mock0 should be initialised in the server"

    mock_module = mqttio.gpio_modules["mock"]
    assert (
        pin in mock_module.pin_configs
    ), "The config for mock0 should be initialised in the gpio module"

    setup_pin = mock_module.setup_pin.__wrapped__
    setup_pin_call_config_pins = [x[1]["pin"] for x in setup_pin.call_args_list]
    assert (
        pin in setup_pin_call_config_pins
    ), "GPIO module's setup_pin() method should have been called for mock0"

    mock0_call_args = None
    for call_args, _ in mock_module.setup_interrupt.call_args_list:
        if call_args[3]["name"] == "mock0":
            mock0_call_args = call_args
    assert mock0_call_args is None, "setup_interrupt() should not be called for mock0"

    poller_task_pin_names = [
        t.get_coro().cr_frame.f_locals["in_conf"]["name"]
        for t in mqttio.unawaited_tasks
        if t.get_coro().__name__ == "digital_input_poller"
    ]
    assert (
        "mock0" in poller_task_pin_names
    ), "digital_input_poller task should be added to the unawaited tasks list for mock0 input"

    poller_task_pin_names = [
        t.get_coro().cr_frame.f_locals["in_conf"]["name"]
        for t in asyncio.Task.all_tasks(loop=mqttio.loop)
        if t.get_coro().__name__ == "digital_input_poller"
    ]
    assert (
        "mock0" in poller_task_pin_names
    ), "digital_input_poller task should be added to the task loop for mock0 input"

    assert not mock_module.remote_interrupt_for(
        pin
    ), "Should not be configured as a remote interrupt"


def test_init_digital_inputs_int(mqttio_mock_digital_inputs: MqttIo):
    """
    Check the initialisation process done for a digital input configured as an interrupt.
    """
    pin = 1
    mqttio = mqttio_mock_digital_inputs
    mqttio._init_gpio_modules()
    mqttio._init_digital_inputs()
    assert (
        "mock1" in mqttio.digital_input_configs
    ), "The config for mock1 should be initialised in the server"

    mock_module = mqttio.gpio_modules["mock"]
    assert (
        pin in mock_module.pin_configs
    ), "The config for mock1 should be initialised in the gpio module"

    setup_pin = mock_module.setup_pin.__wrapped__
    setup_pin_call_config_pins = [x[1]["pin"] for x in setup_pin.call_args_list]
    assert (
        pin in setup_pin_call_config_pins
    ), "GPIO module's setup_pin() method should have been called for mock1"

    mock1_call_args = None
    for call_args, _ in mock_module.setup_interrupt.call_args_list:
        if call_args[3]["name"] == "mock1":
            mock1_call_args = call_args

    assert mock1_call_args is not None, "setup_interrupt() should be called for mock1"
    assert (
        mock1_call_args[1] == InterruptEdge.RISING
    ), "mock1 should be configured with 'rising' interrupt edge"

    poller_task_pin_names = [
        t.get_coro().cr_frame.f_locals["in_conf"]["name"]
        for t in mqttio.unawaited_tasks
        if t.get_coro().__name__ == "digital_input_poller"
    ]
    assert (
        "mock1" not in poller_task_pin_names
    ), "digital_input_poller task should not be added to the unawaited tasks list for mock1 input"

    poller_task_pin_names = [
        t.get_coro().cr_frame.f_locals["in_conf"]["name"]
        for t in asyncio.Task.all_tasks(loop=mqttio.loop)
        if t.get_coro().__name__ == "digital_input_poller"
    ]
    assert (
        "mock1" not in poller_task_pin_names
    ), "digital_input_poller task should not be added to the task loop for mock1 input"

    assert not mock_module.remote_interrupt_for(
        pin
    ), "Should not be configured as a remote interrupt"


def test_init_digital_inputs_int_for(mqttio_mock_digital_inputs: MqttIo):
    """
    Check the initialisation process done for a digital input configured as an interrupt
    for another pin.
    """
    pin = 2
    mqttio = mqttio_mock_digital_inputs
    mqttio._init_gpio_modules()
    mqttio._init_digital_inputs()
    assert (
        "mock2" in mqttio.digital_input_configs
    ), "The config for mock2 should be initialised in the server"

    mock_module = mqttio.gpio_modules["mock"]
    assert (
        pin in mock_module.pin_configs
    ), "The config for mock2 should be initialised in the gpio module"

    setup_pin = mock_module.setup_pin.__wrapped__
    setup_pin_call_config_pins = [x[1]["pin"] for x in setup_pin.call_args_list]
    assert (
        pin in setup_pin_call_config_pins
    ), "GPIO module's setup_pin() method should have been called for mock2"

    mock2_call_args = None
    for call_args, _ in mock_module.setup_interrupt.call_args_list:
        if call_args[3]["name"] == "mock2":
            mock2_call_args = call_args

    assert mock2_call_args is not None, "setup_interrupt() should be called for mock2"
    assert (
        mock2_call_args[1] == InterruptEdge.FALLING
    ), "mock2 should be configured with 'falling' interrupt edge"

    poller_task_pin_names = [
        t.get_coro().cr_frame.f_locals["in_conf"]["name"]
        for t in mqttio.unawaited_tasks
        if t.get_coro().__name__ == "digital_input_poller"
    ]
    assert (
        "mock2" in poller_task_pin_names
    ), "digital_input_poller task should be added to the unawaited tasks list for mock2 input"

    poller_task_pin_names = [
        t.get_coro().cr_frame.f_locals["in_conf"]["name"]
        for t in asyncio.Task.all_tasks(loop=mqttio.loop)
        if t.get_coro().__name__ == "digital_input_poller"
    ]
    assert (
        "mock2" in poller_task_pin_names
    ), "digital_input_poller task should be added to the task loop for mock2 input"

    assert mock_module.remote_interrupt_for(pin) == [
        "mock0"
    ], "mock2 should be configured as a remote interrupt for mock0"


def test_init_digital_outputs_event_sub(mqttio_mock_digital_outputs: MqttIo):
    """"""
    mqttio = mqttio_mock_digital_outputs
    mqttio._init_gpio_modules()

    assert (
        not mqttio.digital_output_configs
    ), "digital_output_configs should not be initialised yet"
    mqttio._init_digital_outputs()
    assert (
        "mock0" in mqttio.digital_output_configs
    ), "mock0 should have its config initialised in the server"

    assert DigitalOutputChangedEvent in mqttio.event_bus._listeners
    assert mqttio.event_bus._listeners[
        DigitalOutputChangedEvent
    ], "Should be an event subscription for DigitalOutputChangedEvent"
    assert "publish_callback" in [
        x.__name__ for x in mqttio.event_bus._listeners[DigitalOutputChangedEvent]
    ], "publish_callback() should be subscribed to DigitalOutputChangedEvent"


def test_init_digital_outputs(mqttio_mock_digital_outputs: MqttIo):
    """"""
    mqttio = mqttio_mock_digital_outputs
    mqttio._init_gpio_modules()
    mqttio._init_digital_outputs()

    mock_module = mqttio.gpio_modules["mock"]
    setup_pin = mock_module.setup_pin.__wrapped__
    assert setup_pin.called, "setup_pin() should be called for the mock0 output"
    _, call_kwargs = setup_pin.call_args
    assert (
        call_kwargs["name"] == "mock0"
    ), "setup_pin() should be called with the mock0 name"
    assert (
        call_kwargs["direction"] == PinDirection.OUTPUT
    ), "setup_pin() should be called with PinDirection.OUTPUT"

    assert all(
        (
            "mock" in mqttio.module_output_queues,
            isinstance(mqttio.module_output_queues["mock"], asyncio.Queue),
        )
    ), "mock module should have an output queue initialised"

    digital_output_loop_task_queues = {
        t.get_coro().cr_frame.f_locals["queue"]
        for t in mqttio.unawaited_tasks
        if t.get_coro().__name__ == "digital_output_loop"
    }
    assert (
        mqttio.module_output_queues["mock"] in digital_output_loop_task_queues
    ), "digital_output_loop task should be added to the unawaited_tasks list for the mock module"

    digital_output_loop_task_queues = {
        t.get_coro().cr_frame.f_locals["queue"]
        for t in asyncio.Task.all_tasks(loop=mqttio.loop)
        if t.get_coro().__name__ == "digital_output_loop"
    }
    assert (
        mqttio.module_output_queues["mock"] in digital_output_loop_task_queues
    ), "digital_output_loop task should be added to the task loop for the mock module"
