import pytest
import yaml
from mqtt_io.config import get_main_schema, validate_and_normalise_config
from mqtt_io.exceptions import ConfigValidationFailed


def prepare_config(yaml_config: str) -> dict:
    schema = get_main_schema()
    config = yaml.safe_load(yaml_config)
    return validate_and_normalise_config(config, schema)


def test_single_gpio_module():
    assert prepare_config(
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
        prepare_config(
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
    assert prepare_config(
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
        prepare_config(
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
