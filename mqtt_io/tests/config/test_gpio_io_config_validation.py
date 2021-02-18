import pytest

from ...exceptions import ConfigValidationFailed
from ...server import MqttIo
from ..utils import validate_config


def test_validate_digital_input_extra_val_good():
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


# def test_validate_digital_input_extra_val_bad():
#     mqttio = MqttIo(
#         validate_config(
#             """
# mqtt:
#     host: localhost

# gpio_modules:
#     - name: mock
#       module: test.mock

# digital_inputs:
#     - name: mock0
#       module: mock
#       pin: 0
#       something_undefined: oops
# """
#         )
#     )
#     mqttio._init_gpio_modules()
#     with pytest.raises(ConfigValidationFailed):
#         mqttio._init_digital_inputs()
