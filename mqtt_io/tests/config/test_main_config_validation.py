import pytest

from ...exceptions import ConfigValidationFailed
from ..utils import validate_config


def test_single_gpio_module() -> None:
    assert validate_config(
        """
mqtt:
    host: localhost

gpio_modules:
    - name: mock
      module: test.mock
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
