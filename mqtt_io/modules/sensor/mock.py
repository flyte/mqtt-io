"""
Mock Sensor module for use with the tests.
"""

from unittest.mock import Mock

from ...types import ConfigType, SensorValueType
from . import GenericSensor

REQUIREMENTS = ()
CONFIG_SCHEMA = {"test": {"type": 'boolean', "required": False, "default": False}}


# pylint: disable=useless-super-delegation
class Sensor(GenericSensor):
    """
    Mock Sensor class for use with the tests.
    """

    def __init__(self, config: ConfigType):
        self.setup_module = Mock()  # type: ignore[assignment]
        self.setup_sensor = Mock()  # type: ignore[assignment]
        self.get_value = Mock(return_value=1)  # type: ignore[assignment]
        super().__init__(config)

    def setup_module(self) -> None:
        return super().setup_module()

    def setup_sensor(self, sens_conf: ConfigType) -> None:
        return super().setup_sensor(sens_conf)

    def get_value(self, sens_conf: ConfigType) -> SensorValueType:
        return super().get_value(sens_conf)
