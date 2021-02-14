import warnings

import pytest
import yaml
from mqtt_io.config import get_main_schema, validate_and_normalise_config

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


def test_init_digital_inputs(mqttio_mock_digital_inputs: MqttIo):
    mqttio = mqttio_mock_digital_inputs
    assert not mqttio.digital_input_configs

    mqttio._init_gpio_modules()
    mqttio._init_digital_inputs()
