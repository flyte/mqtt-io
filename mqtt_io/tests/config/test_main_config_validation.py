"""
Tests for validating and normalising the main config using the static schema. This doesn't
include any extra schemas added to the modules in module.CONFIG_SCHEMA or extra schemas
added to the module classes in module.GPIO.PIN_SCHEMA, module.GPIO.INPUT_SCHEMA etc.
"""

import pytest

from ...exceptions import ConfigValidationFailed
from ..utils import validate_config


def test_no_gpio_io() -> None:
    """
    GPIO modules without digital_inputs or digital_outputs are useless. This should fail.
    """
    with pytest.raises(ConfigValidationFailed):
        validate_config(
            """
mqtt:
    host: localhost

gpio_modules:
    - name: mock
      module: test.mock
"""
        )


def test_ok_gpio_config() -> None:
    """
    Valid config of GPIO module configured with a digital input and a digital output.
    """
    assert validate_config(
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

digital_outputs:
    - name: mock1
      module: mock
      pin: 1
"""
    )


def test_gpio_io_pin_listed_twice_digital_input() -> None:
    """
    Should not be able to configure a module's pin twice in digital_inputs.
    """
    with pytest.raises(ConfigValidationFailed):
        validate_config(
            """
mqtt:
    host: localhost

gpio_modules:
    - name: mock
      module: test.mock

digital_inputs:
    - name: mockA
      module: mock
      pin: 0
    
    - name: mockB
      module: mock
      pin: 0
"""
        )


def test_gpio_io_pin_listed_twice_digital_output() -> None:
    """
    Should not be able to configure a module's pin twice in digital_outputs.
    """
    with pytest.raises(ConfigValidationFailed):
        validate_config(
            """
mqtt:
    host: localhost

gpio_modules:
    - name: mock
      module: test.mock

digital_outputs:
    - name: mockA
      module: mock
      pin: 0
    
    - name: mockB
      module: mock
      pin: 0
"""
        )


def test_gpio_io_pin_listed_both_digital_inputs_digital_outputs() -> None:
    """
    Should not be able to configure a module's pin in digital_inputs and digital_outputs.
    """
    with pytest.raises(ConfigValidationFailed):
        validate_config(
            """
mqtt:
    host: localhost

gpio_modules:
    - name: mock
      module: test.mock

digital_inputs:
    - name: mockA
      module: mock
      pin: 0

digital_outputs:
    - name: mockB
      module: mock
      pin: 0
"""
        )


def test_gpio_io_pin_number_used_across_modules() -> None:
    """
    Should not raise an error if the same pin number is used across modules.
    """
    assert validate_config(
        """
mqtt:
    host: localhost

gpio_modules:
    - name: mock1
      module: test.mock
    
    - name: mock2
      module: test.mock

digital_inputs:
    - name: mockA
      module: mock1
      pin: 0

digital_outputs:
    - name: mockB
      module: mock2
      pin: 0
"""
    )


def test_duplicate_gpio_module() -> None:
    with pytest.raises(ConfigValidationFailed):
        validate_config(
            """
mqtt:
    host: localhost

gpio_modules:
    - name: mock
      module: test.mock

    - name: mock
      module: test.mock
"""
        )


def test_single_digital_input() -> None:
    assert validate_config(
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
"""
    )


def test_duplicate_digital_input() -> None:
    with pytest.raises(ConfigValidationFailed):
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

    - name: mock0
      module: mock
      pin: 1
"""
        )


def test_interrupt_for_non_interrupt_pin() -> None:
    with pytest.raises(ConfigValidationFailed):
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

    - name: mock1
      module: mock
      pin: 1
      interrupt: rising
      interrupt_for:
        - mock0
"""
        )


def test_interrupt_for_no_interrupt() -> None:
    with pytest.raises(ConfigValidationFailed):
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
      interrupt_for:
        - mock0
"""
        )


def test_interrupt_for_self() -> None:
    with pytest.raises(ConfigValidationFailed):
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
      interrupt: rising
      interrupt_for:
        - mock0
"""
        )
