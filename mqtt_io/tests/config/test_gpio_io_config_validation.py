"""
Tests for the validation of IO config sections such as digital_outputs and sensor_inputs.
"""

import pytest

from ...exceptions import ConfigValidationFailed
from ...server import MqttIo
from ..utils import validate_config


# pylint: disable=protected-access


def test_validate_digital_input_extra_val_good() -> None:
    """
    Mock adapter provides a PIN_CONFIG schema that includes a boolean called 'test', so
    adding this value in the IO config should be valid.
    """
    mqttio = MqttIo(
        validate_config(
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
      test: yes
"""
        )
    )
    mqttio._init_gpio_modules()
    mqttio._init_digital_inputs()


def test_validate_digital_input_extra_val_bad() -> None:
    """
    Mock adapter does not specify a 'something_undefined' config entry in PIN_SCHEMA or
    INPUT_SCHEMA, so this should fail validation.
    """
    mqttio = MqttIo(
        validate_config(
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
      something_undefined: oops
"""
        )
    )
    mqttio._init_gpio_modules()
    with pytest.raises(ConfigValidationFailed):
        mqttio._init_digital_inputs()
