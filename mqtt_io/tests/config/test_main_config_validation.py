import pytest
import yaml

from ...config import validate_and_normalise_main_config
from ...exceptions import ConfigValidationFailed
from ...types import ConfigType
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


def test_duplicate_gpio_module():
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


def test_single_digital_input():
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


def test_duplicate_digital_input():
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


def test_interrupt_for_non_interrupt_pin():
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


def test_interrupt_for_no_interrupt():
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


def test_interrupt_for_self():
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
